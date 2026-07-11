#!/usr/bin/env python3
from __future__ import annotations
import argparse,base64,csv,hashlib,html,json,mimetypes,os,re,socket,sqlite3,struct,subprocess,sys,threading,time,urllib.error,urllib.parse,urllib.request
from dataclasses import asdict,dataclass,field
from datetime import date,datetime,timedelta,timezone
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo
REPO_ROOT=Path(__file__).resolve().parents[2]; APP_DIR=REPO_ROOT/'apps/predictive-weekly-planning'
LOCAL_ROOT=REPO_ROOT/'.local/canvas-llm/phase-22-predictive-weekly-planning'; DEFAULT_DB_PATH=LOCAL_ROOT/'workstation.sqlite3'
RAW_IMPORT_PATH=REPO_ROOT/'.local/pacing-imports/2025-2026-reagan-pacing-guide.csv'; SYNTHETIC_FIXTURE_PATH=REPO_ROOT/'fixtures/canvas-llm/phase-22/synthetic-pacing-guide.csv'; COMMITTED_DEMO_PATH=APP_DIR/'data/phase22-demo.json'
UTC=timezone.utc; EASTERN=ZoneInfo('America/New_York'); WEEKDAYS=['Monday','Tuesday','Wednesday','Thursday','Friday']
WEEKLY_STATES={'not_started','in_progress','ready_for_review','approved','scheduled','partially_deployed','deployed','needs_revision','archived'}
SUBJECTS=[{'id':'math','name':'Math'},{'id':'reading','name':'Reading'},{'id':'spelling','name':'Spelling'},{'id':'language-arts','name':'Language Arts'},{'id':'history','name':'History'},{'id':'science','name':'Science'}]
PHASE22_ARTIFACT_CLASSES={'synthetic-curriculum','teacher-planning','public-resource-metadata'}
SELECTED_WEEK_STORAGE_KEY='phase22.selectedWeekCode'
DATE_RE=re.compile(r'\b(?:\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2}(?:,\s*\d{4})?)\b',re.I)
WEEKDAY_RE=re.compile(r'\b(Monday|Tuesday|Wednesday|Thursday|Friday|Mon\.?|Tue\.?|Tues\.?|Wed\.?|Thu\.?|Thurs\.?|Fri\.?)\b',re.I)
LESSON_RE=re.compile(r'\b(?:lesson|less\.?|l)\s*#?\s*(\d+)\b',re.I); TEST_RE=re.compile(r'\b(?:test|assessment)\s*#?\s*(\d+)\b',re.I)
EMAIL_RE=re.compile(r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b',re.I); SENSITIVE_NAME_RE=re.compile(r'\b(?:Student|Learner)\s+[A-Z][A-Za-z-]+\b')
STUDENT_RESULT_RE=re.compile(r'\b(student|learner|score|scores|scored|gradebook|passed|failed|pass/fail|assessment results?|percent|individual|iep|504|accommodation|parent|guardian)\b',re.I)
NUMERIC_SCORE_RE=re.compile(r'\b(?:\d{1,3}\s*/\s*\d{1,3}|\d{1,3}\s*out of\s*\d{1,3}|\d{1,3}\s*%)',re.I)
INSTRUCTIONAL_RE=re.compile(r'\b(lesson|test|activity|lab|review|study guide|checkout|writing|project|benchmark|no school|field trip|unit|chapter|quiz|exam|continue|read|vocab|grammar|spelling|experiment|assessment|science|history)\b',re.I)
BLUE,MAGENTA,DGRAY,WHITE='#0065a7','#c51062','#333333','#ffffff'
DAY_BLOCK_IDS=['kl_activities2','kl_custom_block_4','kl_custom_block_3','kl_custom_block_2','kl_custom_block_1']
DATE_RANGE_RE=re.compile(r'([A-Za-z]+)\s+(\d{1,2})[–\-](\d{1,2}),?\s*(\d{4})')
MONTHS={'January':1,'February':2,'March':3,'April':4,'May':5,'June':6,'July':7,'August':8,'September':9,'October':10,'November':11,'December':12}
CHECKOUT_FLUENCY_CONFIRMED={str(n):{'wpm':100,'maxErrors':2} for n in range(1,8)}
CHECKOUT_FLUENCY_CONFIRMED.update({str(n):{'wpm':115,'maxErrors':2} for n in range(8,11)})
CHECKOUT_FLUENCY_CONFIRMED.update({str(n):{'wpm':130,'maxErrors':2} for n in range(11,14)})
READING_TEST_RE=re.compile(r'\bReading\s+Test\s+(\d+)\b',re.I); CHECKOUT_RE=re.compile(r'\bCheckout\s+(\d+)\b',re.I)
_instructional_weeks_cache=None
def parse_instructional_date_range(text):
    clean=compact(str(text or '').replace('&nbsp;',' ')); m=DATE_RANGE_RE.search(clean)
    if not m: return None,None
    month,d1,d2,year=m.group(1),m.group(2),m.group(3),int(m.group(4))
    if month not in MONTHS: return None,None
    return date(year,MONTHS[month],int(d1)).isoformat(),date(year,MONTHS[month],int(d2)).isoformat()
def load_instructional_weeks():
    global _instructional_weeks_cache
    if _instructional_weeks_cache: return _instructional_weeks_cache
    raw=rjson('canvas/instructional-weeks-2026-2027.json'); weeks=[]
    for w in raw['weeks']:
        starts,ends=parse_instructional_date_range(w.get('displaySubtitle') or '')
        if not starts:
            tail=w.get('pageTitle','').split(' - ',1); starts,ends=parse_instructional_date_range(tail[1] if len(tail)>1 else w.get('pageTitle',''))
        weeks.append({**w,'code':canonical_week_code(w.get('code')), 'startsOn':starts,'endsOn':ends,'displaySubtitle':compact(w.get('displaySubtitle','').replace('&nbsp;',' '))})
    _instructional_weeks_cache=weeks; return weeks
def instructional_week_for_date(d):
    ds=d.isoformat() if isinstance(d,date) else str(d)
    for w in load_instructional_weeks():
        if w['startsOn'] and w['endsOn'] and w['startsOn']<=ds<=w['endsOn']: return w
    return None
def instructional_week_by_starts_on(starts_on):
    for w in load_instructional_weeks():
        if w['startsOn']==starts_on: return w
    return None
def instructional_week_by_code(code):
    code=canonical_week_code(code)
    for w in load_instructional_weeks():
        if w['code']==code: return w
    return None
def next_instructional_week(week):
    weeks=load_instructional_weeks()
    for i,w in enumerate(weeks):
        if w['code']==week['code'] and i+1<len(weeks): return weeks[i+1]
    return None
def week_has_saved_work(workstation,starts_on,conn=None):
    own=conn is None; conn=conn or workstation.connect()
    try:
        row=conn.execute('SELECT id FROM weekly_plans WHERE starts_on=?',(starts_on,)).fetchone()
        if not row: return False
        return bool(conn.execute('SELECT 1 FROM daily_subject_entries WHERE weekly_plan_id=? AND (version>1 OR updated_by NOT IN ("system","generator","importer") OR lesson<>"" OR title<>"" OR in_class<>"" OR at_home<>"") LIMIT 1',(row['id'],)).fetchone())
    finally:
        if own: conn.close()
def resolve_reading_test(n:int):
    if not 1<=n<=14: raise ValueError('Reading Test number must be 1-14')
    end=n*10; start=end-9
    return {'testNumber':n,'title':f'RM4: Reading Test {n}','lessonRange':{'start':start,'end':end},'assignmentGroup':'Tests/Assessments','points':100,'gradeDisplay':'Percentage','submissionType':'On Paper','assignedTo':'All Students','dueTime':'12:00 AM unresolved'}
def resolve_checkout(n:int):
    if not 1<=n<=13: raise ValueError('Checkout number must be 1-13')
    m=rjson('reading/reading-mastery-4/checkout-passage-map.json')['checkouts'][str(n)]; flu=CHECKOUT_FLUENCY_CONFIRMED.get(str(n),{})
    return {'checkoutNumber':n,'readingTestNumber':n,'title':f'RM4: Checkout {n}','sourceCheckoutKey':m['sourceCheckoutKey'],'passage':m['passage'],'bookVolume':m['bookVolume'],'page':m['page'],'fluency':flu,'assignmentGroup':'Checkouts','points':100,'gradeDisplay':'Percentage','submissionType':'On Paper','assignedTo':'All Students','dueTime':'12:00 AM unresolved','checkoutStudyGuideAllowed':False}
def reading_checkout_number(n:int):
    return n if 1<=n<=13 else None
def reading_test_description(test_num:int,has_study_guide=False):
    rt=resolve_reading_test(test_num); lr=rt['lessonRange']; base=f"Review Lessons {lr['start']}-{lr['end']}, including vocabulary and story details."
    return base+(' Use the attached study guide to help you review.' if has_study_guide else '')
def checkout_description(n:int):
    c=resolve_checkout(n); lines=['Target Fluency Goal']
    if c['fluency'].get('wpm'): lines.append(f"{c['fluency']['wpm']} words per minute")
    else: lines.append('[WPM target unresolved]')
    if c['fluency'].get('maxErrors') is not None: lines.append(f"{c['fluency']['maxErrors']} or fewer errors")
    elif not c['fluency']: lines.append('[Maximum errors unresolved]')
    lines+=['Tracking and tapping','Read out loud every day',f"Practice passage: {c['passage']}",f"{c['bookVolume']}, page {c['page']}"]
    return '\n'.join(lines)
def reading_assessment_family(n:int,test_day:str):
    fid=stable_id('reading-assessment-family',n,test_day); rt=resolve_reading_test(n); checkout_number=reading_checkout_number(n); co=resolve_checkout(n) if checkout_number else None
    warnings=[]
    if co and not co['fluency'].get('wpm'): warnings.append(f"Checkout {n} WPM target unresolved; owner source required.")
    if co and co['fluency'].get('maxErrors') is None and str(n) not in CHECKOUT_FLUENCY_CONFIRMED: warnings.append(f"Checkout {n} maximum-error target unresolved.")
    return {'assessmentFamilyId':fid,'readingTestNumber':n,'checkoutNumber':checkout_number,'writtenTestDate':test_day,'checkoutDate':test_day if co else None,'readingTest':rt,'checkout':co,'announcementDraft':stable_id('reading-test-announcement',fid),'sourceCheckoutKey':co['sourceCheckoutKey'] if co else None,'checkoutStudyGuideAllowed':False,'warnings':warnings}
def reading_announcement_body(fam,has_study_guide=False):
    rt,co=fam['readingTest'],fam['checkout']; lr=rt['lessonRange']; lines=['Hello Families,',f"Assessment date: {fam['writtenTestDate']}",f"Reading Test {rt['testNumber']} covers Lessons {lr['start']}-{lr['end']}.", 'Review vocabulary and story details.']
    if has_study_guide: lines.append('Reading Test Study Guide attached or linked when verified.')
    if co:
        lines+=[f"Checkout {co['checkoutNumber']} fluency practice:"]
        if co['fluency'].get('wpm'): lines.append(f"Target: {co['fluency']['wpm']} words per minute")
        else: lines.append('Target fluency: [unresolved]')
        if co['fluency'].get('maxErrors') is not None: lines.append(f"Maximum errors: {co['fluency']['maxErrors']}")
        else: lines.append('Maximum errors: [unresolved]')
        lines+=['Use tracking and tapping.','Read out loud every day.',f"Practice passage: {co['passage']} ({co['bookVolume']}, page {co['page']})."]
    lines+=['Thank you,','Mr. Reagan']
    return '\n'.join(lines)
def parse_reading_quick_create(text):
    rt=READING_TEST_RE.search(text or ''); co=CHECKOUT_RE.search(text or ''); d=parse_date(text,2026)
    if not rt: return None
    test_num=int(rt.group(1))
    checkout_num=int(co.group(1)) if co and 1<=int(co.group(1))<=13 else reading_checkout_number(test_num)
    return {'readingTestNumber':test_num,'checkoutNumber':checkout_num,'date':d}
def serialize_row(table,row):
    rec=dict(row)
    if table=='daily_subject_entries': rec['resources']=jl(rec.get('resources'),[]); rec['resolver_output']=jl(rec.get('resolver_output'),{}); rec['validation']=jl(rec.get('validation'),[])
    elif table=='pacing_entries': rec['payload']=jl(rec.get('payload'),{})
    elif table=='weekly_plans': rec['deployment_status']=jl(rec.get('deployment_status'),{}); rec['payload']=jl(rec.get('payload'),{})
    elif table=='drafts': rec['payload']=jl(rec.get('payload'),{})
    return rec
def patch_response(table,row,fields):
    rec=serialize_row(table,row); out={'record':rec,'version':rec['version'],'updatedAt':rec['updated_at']}
    for k in fields:
        if k in rec: out[k]=rec[k]
    return out
@dataclass
class SchoolYear: id:str; label:str; startsOn:str; endsOn:str
@dataclass
class InstructionalCalendar: schoolYear:str; weekdays:list[str]; closures:list[dict[str,str]]=field(default_factory=list)
@dataclass
class SubjectDefinition: id:str; name:str; columnHints:list[str]=field(default_factory=list)
@dataclass
class PacingEntry:
    id:str; schoolYear:str; sourceYear:str; date:str; weekIndex:int; weekday:str; subjectId:str; rawInstructionalText:str; normalizedTitle:str; entryType:str; sequenceNumber:str|None; source:str; predictionConfidence:float; teacherApproved:bool; actualStatus:str; movedFromDate:str|None=None; notes:str=''
@dataclass
class YearlyPacingGuide: id:str; schoolYear:SchoolYear; instructionalCalendar:InstructionalCalendar; subjects:list[SubjectDefinition]; entries:list[PacingEntry]
@dataclass
class ImportReport: sourcePath:str; sourceKind:str; sourcePresent:bool; rawRowsScanned:int; entriesImported:int; excludedCells:int; unresolvedCells:int; generatedAt:str; notes:list[str]
def now_utc(): return datetime.now(UTC).replace(microsecond=0).isoformat().replace('+00:00','Z')
def stable_id(*p): return 'p22-'+hashlib.sha256('|'.join(map(str,p)).encode()).hexdigest()[:16]
def compact(v): return ' '.join(str(v).replace('\xa0',' ').split())
def canonical_week_code(code):
    token=re.sub(r'[\s_-]+','',compact(code)).upper()
    m=re.fullmatch(r'Q([1-4])W0*(\d{1,2})',token)
    return f"Q{m.group(1)}W{int(m.group(2))}" if m else token
def safe_repo_relative(path):
    p=Path(path)
    try:
        return str(p.relative_to(REPO_ROOT))
    except Exception:
        return str(p)
def jd(v): return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def jl(v,d=None): return d if v in (None,'') else json.loads(v)
def contains_sensitive_content(t):
    v=compact(t); low=v.lower(); return bool(v and (EMAIL_RE.search(v) or SENSITIVE_NAME_RE.search(v) or (STUDENT_RESULT_RE.search(v) and NUMERIC_SCORE_RE.search(v)) or ('assessment' in low and 'result' in low and ('pass/fail' in low or 'scored' in low)) or ('guardian' in low and 'comment' in low)))
def no_sensitive_payload(x):
    if isinstance(x,dict): return all(no_sensitive_payload(v) for v in x.values())
    if isinstance(x,list): return all(no_sensitive_payload(v) for v in x)
    return not contains_sensitive_content(x) if isinstance(x,str) else True
def phase22_artifact_classification(payload):
    if isinstance(payload,dict):
        return payload.get('artifactClassification') or payload.get('classification') or payload.get('privacyBoundary',{}).get('classification')
    return None
def phase22_contains_student_data(payload):
    if isinstance(payload,dict):
        if 'containsStudentData' in payload: return bool(payload.get('containsStudentData'))
        privacy=payload.get('privacyBoundary')
        if isinstance(privacy,dict) and 'studentDataAllowed' in privacy: return bool(privacy.get('studentDataAllowed'))
        if 'student_data' in payload: return bool(payload.get('student_data'))
    return False
def phase22_sensitive_payload_issues(payload,path='root'):
    issues=[]
    if isinstance(payload,dict):
        classification=phase22_artifact_classification(payload)
        if classification and classification not in PHASE22_ARTIFACT_CLASSES:
            issues.append(f"{path}:unapproved-classification")
        if 'containsStudentData' in payload and payload['containsStudentData'] is not False:
            issues.append(f"{path}:containsStudentData-not-false")
        if 'artifactClassification' in payload and not payload['artifactClassification']:
            issues.append(f"{path}:missing-classification")
        if 'privacyBoundary' in payload and isinstance(payload['privacyBoundary'],dict) and payload['privacyBoundary'].get('studentDataAllowed') is not False:
            issues.append(f"{path}:studentDataAllowed-not-false")
        for key in ('studentDataAllowed','student_data'):
            if key in payload and payload.get(key) is not False:
                issues.append(f"{path}:{key}-not-false")
        for key,val in payload.items():
            if key in {'privacyBoundary'}:
                issues.extend(phase22_sensitive_payload_issues(val,f"{path}.{key}"))
            elif isinstance(val,(dict,list)):
                issues.extend(phase22_sensitive_payload_issues(val,f"{path}.{key}"))
            elif isinstance(val,str) and contains_sensitive_content(val):
                issues.append(f"{path}.{key}:sensitive-text")
    elif isinstance(payload,list):
        for i,val in enumerate(payload):
            issues.extend(phase22_sensitive_payload_issues(val,f"{path}[{i}]"))
    elif isinstance(payload,str) and contains_sensitive_content(payload):
        issues.append(f"{path}:sensitive-text")
    return issues
def phase22_safe_quarantine_summary(root:Path):
    root=Path(root)
    manifests=[p for p in root.rglob('manifest.json') if p.is_file()]
    course_manifests=[p for p in manifests if p.parent.name.startswith('course-')]
    parsed=[]
    for manifest_path in course_manifests:
        try:
            parsed.append(json.loads(manifest_path.read_text()))
        except Exception:
            parsed.append({})
    student_data_false=sum(1 for item in parsed if item.get('student_data') is False)
    classification='public-resource-metadata' if manifests else 'unknown'
    issues=[]
    for item in parsed:
        if item.get('student_data') is not False: issues.append('student-data-flag')
        if item.get('metadata_only') is not True: issues.append('metadata-only-flag')
        if item.get('canvas_write') is not False: issues.append('canvas-write-flag')
        if item.get('body_ingestion') is not False: issues.append('body-ingestion-flag')
    return {'root':str(root),'classification':classification,'containsStudentData':False,'manifestCount':len(manifests),'courseManifestCount':len(course_manifests),'studentDataFalseCount':student_data_false,'issueCount':len(issues),'safe':not issues}
def phase22_validate_artifact_payload(payload,source='artifact'):
    issues=phase22_sensitive_payload_issues(payload)
    classification=phase22_artifact_classification(payload)
    if classification is None: issues.append('missing-classification')
    elif classification not in PHASE22_ARTIFACT_CLASSES: issues.append('unapproved-classification')
    if phase22_contains_student_data(payload): issues.append('containsStudentData-not-false')
    return {'source':source,'classification':classification,'containsStudentData':phase22_contains_student_data(payload),'issues':issues,'safe':not issues}
class ChromeCDP:
    def __init__(self,ws_url):
        self.ws_url=ws_url
        parsed=urllib.parse.urlparse(ws_url)
        self.host=parsed.hostname or '127.0.0.1'
        self.port=parsed.port or 9222
        self.path=parsed.path or '/'
        if parsed.query:
            self.path+=f'?{parsed.query}'
        self.sock=socket.create_connection((self.host,self.port),timeout=10)
        key=base64.b64encode(os.urandom(16)).decode()
        req=(
            f'GET {self.path} HTTP/1.1\r\n'
            f'Host: {self.host}:{self.port}\r\n'
            'Upgrade: websocket\r\n'
            'Connection: Upgrade\r\n'
            f'Sec-WebSocket-Key: {key}\r\n'
            'Sec-WebSocket-Version: 13\r\n'
            '\r\n'
        ).encode()
        self.sock.sendall(req)
        response=b''
        while b'\r\n\r\n' not in response:
            chunk=self.sock.recv(4096)
            if not chunk: raise RuntimeError('websocket handshake failed')
            response+=chunk
        if b' 101 ' not in response.split(b'\r\n',1)[0]:
            raise RuntimeError('websocket upgrade failed')
        self.next_id=1
        self.buffer=b''
    def close(self):
        try: self.sock.close()
        except Exception: pass
    def _send_frame(self,payload):
        mask=os.urandom(4)
        header=bytearray([0x81])
        length=len(payload)
        if length<126:
            header.append(0x80|length)
        elif length<65536:
            header.append(0x80|126); header.extend(struct.pack('!H',length))
        else:
            header.append(0x80|127); header.extend(struct.pack('!Q',length))
        header.extend(mask)
        masked=bytes(b ^ mask[i%4] for i,b in enumerate(payload))
        self.sock.sendall(bytes(header)+masked)
    def _recv_exact(self,count):
        while len(self.buffer)<count:
            chunk=self.sock.recv(4096)
            if not chunk: raise RuntimeError('websocket closed')
            self.buffer+=chunk
        out,self.buffer=self.buffer[:count],self.buffer[count:]
        return out
    def _recv_frame(self):
        b1,b2=self._recv_exact(2)
        opcode=b1 & 0x0f
        masked=bool(b2 & 0x80)
        length=b2 & 0x7f
        if length==126:
            length=struct.unpack('!H',self._recv_exact(2))[0]
        elif length==127:
            length=struct.unpack('!Q',self._recv_exact(8))[0]
        mask=self._recv_exact(4) if masked else b''
        payload=self._recv_exact(length) if length else b''
        if masked:
            payload=bytes(b ^ mask[i%4] for i,b in enumerate(payload))
        return opcode,payload
    def recv(self):
        while True:
            opcode,payload=self._recv_frame()
            if opcode==0x1:
                return json.loads(payload.decode())
            if opcode==0x9:
                self._send_frame(payload)  # pong
            elif opcode==0x8:
                raise RuntimeError('websocket closed by peer')
    def send(self,message):
        self._send_frame(json.dumps(message).encode())
    def call(self,method,params=None):
        mid=self.next_id; self.next_id+=1
        self.send({'id':mid,'method':method,'params':params or {}})
        while True:
            data=self.recv()
            if data.get('id')==mid:
                if 'error' in data:
                    raise RuntimeError(data['error'].get('message','cdp error'))
                return data.get('result',{})
    def event(self,method):
        while True:
            data=self.recv()
            if data.get('method')==method:
                return data.get('params',{})
    def eval(self,expression,await_promise=False,return_by_value=True):
        result=self.call('Runtime.evaluate',{'expression':expression,'awaitPromise':await_promise,'returnByValue':return_by_value,'userGesture':True})
        if 'exceptionDetails' in result:
            raise RuntimeError(result['exceptionDetails'].get('text','runtime error'))
        return result.get('result',{}).get('value')
def wait_for_http_json(url,timeout=20):
    deadline=time.time()+timeout
    while time.time()<deadline:
        try:
            with urllib.request.urlopen(url,timeout=2) as response:
                return json.loads(response.read())
        except Exception:
            time.sleep(0.25)
    raise RuntimeError(f'timeout waiting for {url}')
def wait_for_condition(cdp,expression,timeout=20):
    deadline=time.time()+timeout
    last=None
    while time.time()<deadline:
        try:
            last=cdp.eval(expression)
            if last:
                return last
        except Exception:
            pass
        time.sleep(0.2)
    raise RuntimeError(f'timeout waiting for condition: {expression} (last={last})')
def rjson(*parts): return json.loads((REPO_ROOT/'config/curriculum'/Path(*parts)).read_text())
def resolve_math_lesson(n:int,homework_override=None):
    if not 1<=n<=120: raise ValueError('Math lesson number must be 1-120')
    p=rjson('math/saxon-math-5/lesson-power-up-map.json')['lessonToPowerUp'].get(str(n));
    if not p: raise ValueError('Missing Power Up mapping')
    return {'lessonNumber':n,'powerUpCode':p,'suggestedHomework':homework_override or ('Odds' if n%2 else 'Evens'),'teacherOverride':homework_override}
def resolve_fact_test(n:int):
    if not 1<=n<=23: raise ValueError('Fact Test number must be 1-23')
    i=rjson('math/saxon-math-5/fact-test-practice-map.json')['tests'].get(str(n));
    if not i: raise ValueError('Missing Fact Test mapping')
    return {'testNumber':n,'powerUpCode':i['powerUpCode'],'practiceDescription':i['practiceDescription']}
def resolve_reading_lesson(n:int):
    if not 1<=n<=140: raise ValueError('Reading lesson number must be 1-140')
    i=rjson('reading/reading-mastery-4/comprehension-location-map.json')['lessons'].get(str(n));
    if not i: raise ValueError('Missing Reading mapping')
    return {'lessonNumber':n,'comprehensionLetter':i['comprehensionLetter'],'page':i['page']}
def resolve_spelling_test(n:int):
    if not 1<=n<=24: raise ValueError('Spelling test number must be 1-24')
    i=rjson('spelling/cumulative-test-word-lists.json')['tests'].get(str(n));
    if not i: raise ValueError('Missing Spelling mapping')
    return {'testNumber':n,'words':i['words'],'focusWords':i.get('focusWords',i['words'][20:25]),'lessonsCovered':i.get('lessonsCovered')}
def resolve_course(school_year,environment,subject,production_target=False):
    m=rjson('canvas-course-mappings.json'); groups=[]
    for key,arch in [('currentProduction',False),('demoSandbox',False)]:
        g=m.get(key,{})
        if g.get('schoolYear')==school_year and g.get('environment')==environment: groups.append((g,arch))
    for g in m.get('archivedReference',[]):
        if g.get('schoolYear')==school_year and g.get('environment')==environment: groups.append((g,True))
    if not groups: raise ValueError('Missing course mapping; school year and environment are required')
    g,arch=groups[0]
    if production_target and arch: raise ValueError('Archived courses cannot be deployment targets')
    if production_target and 'sandbox' in environment: raise ValueError('Sandbox cannot be production target')
    for c in g.get('courses',[]):
        if c.get('subjectId')==subject:
            out=dict(c); out.update({'schoolYear':school_year,'environment':environment,'archived':arch,'deploymentTargetAllowed':not arch and 'sandbox' not in environment}); return out
    raise ValueError('No mapping for subject')
def parse_date(v,fallback_year=2026):
    m=DATE_RE.search(v or '')
    if not m: return None
    tok=m.group(0).replace('.','')
    for fmt in ['%m/%d/%Y','%m/%d/%y','%m/%d','%m-%d-%Y','%m-%d-%y','%m-%d','%b %d, %Y','%B %d, %Y','%b %d','%B %d']:
        try:
            d=datetime.strptime(tok,fmt); y=d.year if '%Y' in fmt or '%y' in fmt else fallback_year; return date(y,d.month,d.day).isoformat()
        except ValueError: pass
    return None
def weekday_for(v,parsed=None):
    m=WEEKDAY_RE.search(v or '')
    if m:
        t=m.group(1).lower().rstrip('.'); return {'mon':'Monday','tue':'Tuesday','tues':'Tuesday','wed':'Wednesday','thu':'Thursday','thurs':'Thursday','fri':'Friday'}.get(t,t.capitalize())
    return date.fromisoformat(parsed).strftime('%A') if parsed else 'Monday'
def entry_type_for(t):
    l=t.lower()
    for typ,needles in [('no-school',('no school','closure')),('test',('test','quiz','exam')),('study-guide',('study guide',)),('lab',('lab','experiment')),('review',('review',)),('checkout',('checkout',)),('writing',('writing','essay','draft')),('project',('project',)),('lesson',('lesson','read'))]:
        if any(n in l for n in needles): return typ
    return 'unresolved'
def sequence_for(t):
    m=LESSON_RE.search(t) or TEST_RE.search(t); return m.group(1) if m else None
def subject_for_column(c): return SUBJECTS[c%len(SUBJECTS)]['id']
def import_pacing_grid(path:Path,source_kind:str):
    rows=[[compact(c) for c in r] for r in csv.reader(path.open(newline='',encoding='utf-8-sig'))]
    imported=[]; excluded=[]; unresolved=[]; cur_dates={}; cur_weekdays={}; week=0; seen=set()
    for ri,row in enumerate(rows):
        dates={ci:parse_date(cell) for ci,cell in enumerate(row) if DATE_RE.fullmatch(cell or '')}; dates={k:v for k,v in dates.items() if v}
        if len(dates)>=2:
            week+=1; cur_dates=dates; cur_weekdays={ci:weekday_for(row[ci],d) for ci,d in dates.items()}
            if ri+1<len(rows):
                for ci,d in dates.items(): cur_weekdays[ci]=weekday_for(rows[ri+1][ci] if ci<len(rows[ri+1]) else '',d)
            continue
        for ci,cell in enumerate(row):
            if not cell or DATE_RE.fullmatch(cell) or WEEKDAY_RE.fullmatch(cell): continue
            if contains_sensitive_content(cell): excluded.append({'row':ri+1,'column':ci+1,'reason':'student-or-assessment-result-excluded'}); continue
            if not INSTRUCTIONAL_RE.search(cell):
                if len(cell)>20: unresolved.append({'row':ri+1,'column':ci+1,'reason':'unclassified-non-instructional-cell'})
                continue
            nearest=min(cur_dates,key=lambda x:abs(x-ci)) if cur_dates else ci; parsed=cur_dates.get(nearest)
            if not parsed: unresolved.append({'row':ri+1,'column':ci+1,'reason':'instructional-cell-without-date-anchor'}); continue
            key=(parsed,ci,cell)
            if key in seen: continue
            seen.add(key); imported.append(PacingEntry(stable_id(source_kind,ri+1,ci+1,cell),'2026-2027','2025-2026',parsed,max(week,1),cur_weekdays.get(nearest,weekday_for('',parsed)),subject_for_column(ci),cell,cell[:120],entry_type_for(cell),sequence_for(cell),source_kind,.76 if source_kind=='real-import' else .62,False,'predicted'))
    if not imported:
        start=date(2026,8,17)
        for i,(s,t) in enumerate([('math','Lesson 1 Power Up'),('reading','Lesson 1 comprehension'),('spelling','Test 1 focus words'),('history','Chapter 1 map skills'),('science','Investigation 1 notebook setup')]):
            d=start+timedelta(days=i); imported.append(PacingEntry(stable_id(source_kind,'fallback',i),'2026-2027','synthetic',d.isoformat(),1,d.strftime('%A'),s,t,t,entry_type_for(t),sequence_for(t),source_kind,.42,False,'predicted'))
    entries=sorted(imported,key=lambda e:(e.date,e.subjectId,e.normalizedTitle)); dates=[date.fromisoformat(e.date) for e in entries]
    sy=SchoolYear('2026-2027','2026-2027',min(dates).isoformat(),max(dates).isoformat())
    guide=YearlyPacingGuide('phase-22-yearly-pacing-guide',sy,InstructionalCalendar(sy.id,WEEKDAYS,[]),[SubjectDefinition(s['id'],s['name'],[]) for s in SUBJECTS],entries)
    report=ImportReport(safe_repo_relative(path),source_kind,path.exists(),len(rows),len(entries),len(excluded),len(unresolved),now_utc(),['Only instructional pacing cells are imported.','Excluded-cell reports contain location and reason only.','Raw imports remain ignored local files.'])
    return guide,report,excluded,unresolved
def previous_instructional_day(start:date,no_school:set[str]):
    d=start-timedelta(days=1)
    while d.weekday()>=5 or d.isoformat() in no_school: d-=timedelta(days=1)
    return d
def next_instructional_day(start:date,no_school:set[str]):
    d=start
    while d.weekday()>=5 or d.isoformat() in no_school: d+=timedelta(days=1)
    return d
def math_assessment_family(n:int,test_day:str,no_school:set[str]):
    fact=resolve_fact_test(n); study=previous_instructional_day(date.fromisoformat(test_day),no_school).isoformat(); fid=stable_id('math-assessment-family',n,test_day)
    return {'assessmentFamilyId':fid,'testNumber':n,'writtenTestDate':test_day,'factTestDate':test_day,'studyGuideDate':study,'announcementDraft':stable_id('math-test-announcement',fid),'factTest':fact,'studyGuideSuppressesNormalHomework':True,'suppressionReason':f'Study Guide {n} is the only Math homework before Test {n}.','requiredResources':[f'Study Guide {n} Blank',f'Study Guide {n} Completed',f'Power Up {fact["powerUpCode"]} practice']}
SCHEMA='''
CREATE TABLE IF NOT EXISTS schema_migrations(version INTEGER PRIMARY KEY,applied_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS settings(id TEXT PRIMARY KEY,value TEXT NOT NULL,version INTEGER NOT NULL DEFAULT 1,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,updated_by TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS school_years(id TEXT PRIMARY KEY,label TEXT NOT NULL,starts_on TEXT NOT NULL,ends_on TEXT NOT NULL,version INTEGER NOT NULL DEFAULT 1,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,updated_by TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS instructional_calendars(id TEXT PRIMARY KEY,school_year TEXT NOT NULL,timezone TEXT NOT NULL,weekdays TEXT NOT NULL,version INTEGER NOT NULL DEFAULT 1,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,updated_by TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS no_school_dates(id TEXT PRIMARY KEY,school_year TEXT NOT NULL,date TEXT NOT NULL,reason TEXT NOT NULL,version INTEGER NOT NULL DEFAULT 1,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,updated_by TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS pacing_imports(id TEXT PRIMARY KEY,source_path TEXT NOT NULL,source_kind TEXT NOT NULL,raw_rows_scanned INTEGER NOT NULL,entries_imported INTEGER NOT NULL,excluded_cells INTEGER NOT NULL,unresolved_cells INTEGER NOT NULL,excluded_report TEXT NOT NULL,unresolved_report TEXT NOT NULL,provenance TEXT NOT NULL,version INTEGER NOT NULL DEFAULT 1,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,updated_by TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS pacing_entries(id TEXT PRIMARY KEY,import_id TEXT,school_year TEXT NOT NULL,source_year TEXT NOT NULL,entry_date TEXT NOT NULL,week_index INTEGER NOT NULL,weekday TEXT NOT NULL,subject TEXT NOT NULL,raw_text TEXT NOT NULL,normalized_title TEXT NOT NULL,entry_type TEXT NOT NULL,sequence_number TEXT,status TEXT NOT NULL,teacher_approved INTEGER NOT NULL,notes TEXT NOT NULL,payload TEXT NOT NULL,version INTEGER NOT NULL DEFAULT 1,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,updated_by TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS weekly_plans(id TEXT PRIMARY KEY,school_year TEXT NOT NULL,starts_on TEXT NOT NULL,state TEXT NOT NULL,deployment_status TEXT NOT NULL,validation_state TEXT NOT NULL,payload TEXT NOT NULL,version INTEGER NOT NULL DEFAULT 1,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,updated_by TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS subject_weekly_plans(id TEXT PRIMARY KEY,weekly_plan_id TEXT NOT NULL,subject TEXT NOT NULL,payload TEXT NOT NULL,version INTEGER NOT NULL DEFAULT 1,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,updated_by TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS daily_subject_entries(id TEXT PRIMARY KEY,weekly_plan_id TEXT NOT NULL,subject_plan_id TEXT NOT NULL,subject TEXT NOT NULL,entry_date TEXT NOT NULL,weekday TEXT NOT NULL,lesson TEXT NOT NULL,title TEXT NOT NULL,in_class TEXT NOT NULL,at_home TEXT NOT NULL,materials TEXT NOT NULL,reminders TEXT NOT NULL,tests TEXT NOT NULL,resources TEXT NOT NULL,notes TEXT NOT NULL,resolver_output TEXT NOT NULL,validation TEXT NOT NULL,version INTEGER NOT NULL DEFAULT 1,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,updated_by TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS resources(id TEXT PRIMARY KEY,canonical_name TEXT NOT NULL,original_name TEXT,subject TEXT,curriculum TEXT,resource_type TEXT,variant TEXT,audience TEXT NOT NULL,sensitivity TEXT NOT NULL,verification_status TEXT NOT NULL,sha256 TEXT,local_path TEXT,canvas_metadata TEXT NOT NULL,metadata TEXT NOT NULL,version INTEGER NOT NULL DEFAULT 1,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,updated_by TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS resource_relationships(id TEXT PRIMARY KEY,resource_id TEXT NOT NULL,related_type TEXT NOT NULL,related_id TEXT NOT NULL,relationship TEXT NOT NULL,version INTEGER NOT NULL DEFAULT 1,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,updated_by TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS assignment_families(id TEXT PRIMARY KEY,weekly_plan_id TEXT NOT NULL,subject TEXT NOT NULL,family_type TEXT NOT NULL,sequence_number TEXT NOT NULL,payload TEXT NOT NULL,version INTEGER NOT NULL DEFAULT 1,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,updated_by TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS drafts(id TEXT PRIMARY KEY,weekly_plan_id TEXT NOT NULL,kind TEXT NOT NULL,subject TEXT NOT NULL,title TEXT NOT NULL,body_text TEXT NOT NULL,body_html TEXT NOT NULL,status TEXT NOT NULL,idempotency_key TEXT NOT NULL,payload TEXT NOT NULL,version INTEGER NOT NULL DEFAULT 1,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,updated_by TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS scheduling_intents(id TEXT PRIMARY KEY,weekly_plan_id TEXT NOT NULL,draft_id TEXT,intended_for_utc TEXT,timezone TEXT NOT NULL,payload TEXT NOT NULL,version INTEGER NOT NULL DEFAULT 1,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,updated_by TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS deployment_plans(id TEXT PRIMARY KEY,weekly_plan_id TEXT NOT NULL,status TEXT NOT NULL,payload TEXT NOT NULL,version INTEGER NOT NULL DEFAULT 1,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,updated_by TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS deployment_items(id TEXT PRIMARY KEY,deployment_plan_id TEXT NOT NULL,item_type TEXT NOT NULL,target TEXT NOT NULL,dependency_order INTEGER NOT NULL,status TEXT NOT NULL,approved INTEGER NOT NULL,validated INTEGER NOT NULL,current_year_mapped INTEGER NOT NULL,stale INTEGER NOT NULL,already_deployed INTEGER NOT NULL,unresolved_dependencies TEXT NOT NULL,idempotency_key TEXT NOT NULL,payload TEXT NOT NULL,version INTEGER NOT NULL DEFAULT 1,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,updated_by TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS revisions(id TEXT PRIMARY KEY,record_type TEXT NOT NULL,record_id TEXT NOT NULL,record_version INTEGER NOT NULL,snapshot TEXT NOT NULL,created_at TEXT NOT NULL,created_by TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS audit_history(id TEXT PRIMARY KEY,action TEXT NOT NULL,record_type TEXT NOT NULL,record_id TEXT NOT NULL,detail TEXT NOT NULL,created_at TEXT NOT NULL,updated_by TEXT NOT NULL);
'''
def select_startup_week(workstation,today=None):
    today=today or datetime.now(EASTERN).date(); weeks=load_instructional_weeks(); first_start,last_end=weeks[0]['startsOn'],weeks[-1]['endsOn']
    if today.isoformat()<first_start: return {'mode':'chooser','reason':'before-school-year','week':weeks[0],'startupPrompt':'School year has not started; choose a week.','warning':None}
    if today.isoformat()>last_end: return {'mode':'chooser','reason':'after-school-year','week':weeks[-1],'startupPrompt':'School year has ended; choose a week.','warning':None}
    active=instructional_week_for_date(today)
    if not active:
        nxt=next((w for w in weeks if w['startsOn']>today.isoformat()),weeks[-1])
        return {'mode':'break','reason':'break/no-school period','week':nxt,'startupPrompt':f"No instructional week contains {today.isoformat()}; showing next instructional week {nxt['code']}.",'warning':None}
    if today.weekday()>=5:
        upcoming=instructional_week_for_date(today+timedelta(days=(7-today.weekday())))
        if upcoming and upcoming['code']!=active['code']: active=upcoming
    with workstation.connect() as conn:
        plan=conn.execute('SELECT * FROM weekly_plans WHERE starts_on=?',(active['startsOn'],)).fetchone(); warn=None; target=active
        if plan:
            if plan['state'] in {'partially_deployed','needs_revision'}: warn='Current week has partial deployment or failed validation; reopen it before future deployment.'
            elif plan['state']=='deployed':
                nxt=next_instructional_week(active)
                if nxt and week_has_saved_work(workstation,nxt['startsOn'],conn): target,warn=nxt,'Next week already contains saved work; continuing saved work.'
                elif nxt: target,warn=nxt,'Current week is deployed; advanced to next instructional week.'
        elif week_has_saved_work(workstation,active['startsOn'],conn): warn='Saved work found for selected week.'
    return {'mode':'active','reason':'instructional-week','week':target,'startupPrompt':None,'warning':warn,'instructionalWeeks':weeks}
def default_settings(): return {'timezone':'America/New_York','schoolYear':'2026-2027','environment':'production','autosaveDebounceMs':700,'weeklyScheduleIntent':'Friday 4:00 PM America/New_York','dailyBriefRecipient':'owen.reagan@thalesacademy.org','dailyBriefSchedule':'6:15 AM America/New_York instructional days','canvasWritesAllowed':False,'emailSendsAllowed':False}
class WorkstationDB:
    def __init__(self,path=None): self.path=Path(path or os.environ.get('PHASE22_DB_PATH') or DEFAULT_DB_PATH); self.path.parent.mkdir(parents=True,exist_ok=True); self._lock=threading.Lock()
    def connect(self):
        c=sqlite3.connect(self.path); c.row_factory=sqlite3.Row; c.execute('PRAGMA foreign_keys=ON'); c.execute('PRAGMA journal_mode=WAL'); c.execute('PRAGMA busy_timeout=5000'); return c
    def migrate(self):
        with self.connect() as db:
            db.executescript(SCHEMA); db.execute('INSERT OR IGNORE INTO schema_migrations VALUES(1,?)',(now_utc(),)); db.execute('INSERT OR IGNORE INTO settings(id,value,created_at,updated_at,updated_by) VALUES("app",?,?,?,"system")',(jd(default_settings()),now_utc(),now_utc())); db.execute('INSERT OR IGNORE INTO school_years(id,label,starts_on,ends_on,created_at,updated_at,updated_by) VALUES("2026-2027","2026-2027","2026-08-17","2027-05-28",?,?,"system")',(now_utc(),now_utc())); db.execute('INSERT OR IGNORE INTO instructional_calendars(id,school_year,timezone,weekdays,created_at,updated_at,updated_by) VALUES("2026-2027-default","2026-2027","America/New_York",?,?,?,"system")',(jd(WEEKDAYS),now_utc(),now_utc())); db.commit()
    def backup(self,reason='manual',connection=None):
        b=self.path.parent/'backups'; b.mkdir(parents=True,exist_ok=True); out=b/f'{self.path.stem}-{reason}-{datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")}.sqlite3'
        if self.path.exists():
            src=sqlite3.connect(self.path); dst=sqlite3.connect(out); src.backup(dst); dst.close(); src.close()
        else: out.touch()
        db=connection or self.connect(); db.execute('INSERT INTO audit_history VALUES(?,?,?,?,?,?,?)',(stable_id('audit',reason,out),'manual' if reason=='manual' else reason,'backup',str(out),jd({'path':str(out)}),now_utc(),'system'))
        if not connection: db.commit(); db.close()
        return out
    def seed_from_fixture(self):
        with self.connect() as db:
            if not db.execute('SELECT 1 FROM pacing_entries LIMIT 1').fetchone(): self._save_import(db,*import_pacing_grid(SYNTHETIC_FIXTURE_PATH,'synthetic-fixture'),replace=True)
            if not db.execute('SELECT 1 FROM weekly_plans LIMIT 1').fetchone():
                sel=select_startup_week(self); starts=sel.get('week',{}).get('startsOn') or '2026-07-20'; self.create_week(starts,db)
            db.commit()
    def _save_import(self,db,guide,report,excluded,unresolved,replace=False):
        if replace: db.execute('DELETE FROM pacing_entries')
        iid=stable_id('import',report.generatedAt,report.sourceKind); db.execute('INSERT OR REPLACE INTO pacing_imports(id,source_path,source_kind,raw_rows_scanned,entries_imported,excluded_cells,unresolved_cells,excluded_report,unresolved_report,provenance,created_at,updated_at,updated_by) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',(iid,report.sourcePath,report.sourceKind,report.rawRowsScanned,report.entriesImported,report.excludedCells,report.unresolvedCells,jd(excluded),jd(unresolved),jd(asdict(report)),now_utc(),now_utc(),'importer'))
        for e in guide.entries:
            existing=db.execute('SELECT version,updated_by FROM pacing_entries WHERE id=?',(e.id,)).fetchone()
            if existing and (int(existing['version'])>1 or existing['updated_by'] not in ('importer','system')): continue
            d=asdict(e); db.execute('INSERT OR REPLACE INTO pacing_entries(id,import_id,school_year,source_year,entry_date,week_index,weekday,subject,raw_text,normalized_title,entry_type,sequence_number,status,teacher_approved,notes,payload,version,created_at,updated_at,updated_by) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,COALESCE((SELECT version FROM pacing_entries WHERE id=?),0)+1,COALESCE((SELECT created_at FROM pacing_entries WHERE id=?),?),?,?)',(e.id,iid,e.schoolYear,e.sourceYear,e.date,e.weekIndex,e.weekday,e.subjectId,e.rawInstructionalText,e.normalizedTitle,e.entryType,e.sequenceNumber,e.actualStatus,int(e.teacherApproved),e.notes,jd(d),e.id,e.id,now_utc(),now_utc(),'importer'))
    def create_week(self,starts_on,db=None):
        own=db is None; db=db or self.connect(); wid=stable_id('week',starts_on); iw=instructional_week_by_starts_on(starts_on) or {}
        payload={'startsOn':starts_on,'instructionalWeek':{k:iw.get(k) for k in ('quarter','week','code','startsOn','endsOn','displaySubtitle','pageTitle') if iw.get(k)}}
        db.execute('INSERT OR IGNORE INTO weekly_plans(id,school_year,starts_on,state,deployment_status,validation_state,payload,created_at,updated_at,updated_by) VALUES(?,?,?,?,?,?,?,?,?,?)',(wid,'2026-2027',starts_on,'in_progress',jd({k:'not_started' for k in ['subject_page','assignment_family','newsletter','announcement','daily_brief']}),'needs_validation',jd(payload),now_utc(),now_utc(),'system'))
        for s in [x['id'] for x in SUBJECTS]:
            sid=stable_id('subject',wid,s); db.execute('INSERT OR IGNORE INTO subject_weekly_plans(id,weekly_plan_id,subject,payload,created_at,updated_at,updated_by) VALUES(?,?,?,?,?,?,?)',(sid,wid,s,jd({'subject':s}),now_utc(),now_utc(),'system'))
            for i,wday in enumerate(WEEKDAYS):
                day=(date.fromisoformat(starts_on)+timedelta(days=i)).isoformat(); db.execute('INSERT OR IGNORE INTO daily_subject_entries(id,weekly_plan_id,subject_plan_id,subject,entry_date,weekday,lesson,title,in_class,at_home,materials,reminders,tests,resources,notes,resolver_output,validation,created_at,updated_at,updated_by) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(stable_id('daily',wid,s,day),wid,sid,s,day,wday,'','','','','','','','[]','', '{}','[]',now_utc(),now_utc(),'system'))
        self.generate_week(wid,db)
        if own: db.commit(); db.close()
        return wid
    def create_revision(self,db,table,rid,row,by): db.execute('INSERT INTO revisions VALUES(?,?,?,?,?,?,?)',(stable_id('rev',table,rid,row.get('version'),now_utc()),table,rid,row.get('version',0),jd(row),now_utc(),by))
    def patch_table(self,table,rid,fields,expected_version=None,updated_by='owen'):
        allowed={'weekly_plans':{'state','validation_state','payload'},'daily_subject_entries':{'lesson','title','in_class','at_home','materials','reminders','tests','resources','notes','resolver_output','validation'},'drafts':{'title','body_text','body_html','status','payload'},'pacing_entries':{'entry_date','subject','normalized_title','entry_type','sequence_number','status','teacher_approved','notes','payload'},'resources':{'canonical_name','original_name','subject','curriculum','resource_type','variant','audience','sensitivity','verification_status','local_path','canvas_metadata','metadata','sha256'}}
        f={k:v for k,v in fields.items() if k in allowed.get(table,set())}
        if not f: raise ValueError('no patchable fields')
        with self._lock,self.connect() as db:
            row=db.execute(f'SELECT * FROM {table} WHERE id=?',(rid,)).fetchone()
            if not row: raise KeyError('record not found')
            if expected_version is not None and int(row['version'])!=int(expected_version): return {'conflict':True,'status':409,'serverRecord':serialize_row(table,dict(row)),'version':row['version']}
            self.create_revision(db,table,rid,dict(row),updated_by); vals=list(f.values())+[int(row['version'])+1,now_utc(),updated_by,rid]
            db.execute(f"UPDATE {table} SET {','.join(k+'=?' for k in f)},version=?,updated_at=?,updated_by=? WHERE id=?",vals); db.commit(); updated=db.execute(f'SELECT * FROM {table} WHERE id=?',(rid,)).fetchone(); return patch_response(table,updated,f)
    def list_revisions(self,record_type=None,record_id=None):
        sql='SELECT * FROM revisions WHERE 1=1'; vals=[]
        if record_type: sql+=' AND record_type=?'; vals.append(record_type)
        if record_id: sql+=' AND record_id=?'; vals.append(record_id)
        with self.connect() as db: return [dict(r) for r in db.execute(sql+' ORDER BY created_at DESC LIMIT 200',vals)]
    def restore_revision(self,rev_id,updated_by='owen'):
        self.backup('pre-restore')
        with self.connect() as db:
            rev=db.execute('SELECT * FROM revisions WHERE id=?',(rev_id,)).fetchone(); snap=jl(rev['snapshot'])
            cur=db.execute(f"SELECT * FROM {rev['record_type']} WHERE id=?",(rev['record_id'],)).fetchone(); self.create_revision(db,rev['record_type'],rev['record_id'],dict(cur),updated_by)
            cols=[k for k in snap if k not in {'version','updated_at','updated_by'}]; vals=[snap[k] for k in cols]+[cur['version']+1,now_utc(),updated_by,rev['record_id']]
            db.execute(f"UPDATE {rev['record_type']} SET {','.join(k+'=?' for k in cols)},version=?,updated_at=?,updated_by=? WHERE id=?",vals); db.commit(); return {'restored':True,'revisionId':rev_id}
    def current_week(self,today=None):
        with self.connect() as db:
            sel=select_startup_week(self,today); iw=sel['week']
            if not db.execute('SELECT 1 FROM weekly_plans WHERE starts_on=?',(iw['startsOn'],)).fetchone(): self.create_week(iw['startsOn'],db); db.commit()
            row=db.execute('SELECT * FROM weekly_plans WHERE starts_on=?',(iw['startsOn'],)).fetchone()
            return {'week':row_to_week(db,row),'startup':sel,'startupPrompt':sel.get('startupPrompt'),'warning':sel.get('warning'),'instructionalWeek':iw,'weekChooser':sel.get('mode')=='chooser'}
    def get_week(self,wid):
        with self.connect() as db: return row_to_week(db,db.execute('SELECT * FROM weekly_plans WHERE id=?',(wid,)).fetchone())
    def get_week_by_code(self,code):
        iw=instructional_week_by_code(code)
        if not iw: raise KeyError('week code not found')
        with self.connect() as db:
            if not db.execute('SELECT 1 FROM weekly_plans WHERE starts_on=?',(iw['startsOn'],)).fetchone(): self.create_week(iw['startsOn'],db); db.commit()
            row=db.execute('SELECT * FROM weekly_plans WHERE starts_on=?',(iw['startsOn'],)).fetchone()
            return row_to_week(db,row)
    def import_pacing(self,path,replace=True):
        source=path if Path(path).exists() else SYNTHETIC_FIXTURE_PATH; kind='real-import' if Path(source)==RAW_IMPORT_PATH else 'synthetic-fixture'; g,r,e,u=import_pacing_grid(Path(source),kind)
        with self.connect() as db:
            if replace: self.backup('pre-import',db)
            self._save_import(db,g,r,e,u,replace); db.commit()
        return {'yearlyPacingGuide':asdict(g),'importReport':asdict(r),'excludedCellReport':e,'unresolvedCellReport':u}
    def register_resource(self,payload):
        lp=payload.get('localPath') or payload.get('local_path'); sha=payload.get('sha256'); size=None; mime=payload.get('mimeType')
        if lp and Path(lp).exists():
            h=hashlib.sha256(); f=Path(lp); size=f.stat().st_size; mime=mime or mimetypes.guess_type(lp)[0]
            with f.open('rb') as fh:
                for chunk in iter(lambda:fh.read(1048576),b''): h.update(chunk)
            sha=h.hexdigest()
        rid=payload.get('id') or stable_id('resource',payload.get('canonicalName'),sha or lp or now_utc()); meta={'lessonNumbers':payload.get('lessonNumbers',[]),'testNumbers':payload.get('testNumbers',[]),'powerUpCodes':payload.get('powerUpCodes',[]),'schoolYears':payload.get('schoolYears',['2026-2027']),'fileSize':size,'mimeType':mime}
        with self.connect() as db:
            db.execute('INSERT INTO resources(id,canonical_name,original_name,subject,curriculum,resource_type,variant,audience,sensitivity,verification_status,sha256,local_path,canvas_metadata,metadata,created_at,updated_at,updated_by) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET canonical_name=excluded.canonical_name,sensitivity=excluded.sensitivity,verification_status=excluded.verification_status,version=resources.version+1,updated_at=excluded.updated_at',(rid,payload.get('canonicalName') or 'Untitled resource',payload.get('originalName'),payload.get('subject'),payload.get('curriculum'),payload.get('resourceType'),payload.get('variant'),payload.get('audience','student'),payload.get('sensitivity','student-facing'),payload.get('verificationStatus','unverified'),sha,lp,jd(payload.get('canvasReferences',[])),jd(meta),now_utc(),now_utc(),'owen'))
            db.commit(); return dict(db.execute('SELECT * FROM resources WHERE id=?',(rid,)).fetchone())
    def resources(self,q=None):
        with self.connect() as db: return [dict(r) for r in db.execute('SELECT * FROM resources ORDER BY canonical_name LIMIT 200')]
    def generate_week(self,wid,db=None):
        own=db is None; db=db or self.connect(); rows=[dict(r) for r in db.execute('SELECT * FROM daily_subject_entries WHERE weekly_plan_id=? ORDER BY entry_date,subject',(wid,))]
        for r in rows:
            resolver=resolver_for_daily(r); val=[]
            if r['subject']=='math' and resolver.get('assessmentFamily'):
                for label in resolver['assessmentFamily']['requiredResources']:
                    if not db.execute("SELECT 1 FROM resources WHERE canonical_name LIKE ? AND verification_status='verified'",(f'%{label}%',)).fetchone(): val.append({'severity':'blocking','message':f'Missing verified resource: {label}'})
            if r['subject']=='reading' and resolver.get('assessmentFamily'):
                for wmsg in resolver['assessmentFamily'].get('warnings',[]): val.append({'severity':'warning','message':wmsg})
            db.execute('UPDATE daily_subject_entries SET resolver_output=?,validation=? WHERE id=?',(jd(resolver),jd(val),r['id']))
        replace_drafts(db,wid); replace_deployment(db,wid)
        if own: db.commit(); db.close()
        return self.get_week(wid) if own else {}
def resolver_for_daily(r):
    lesson=int(r['lesson']) if str(r.get('lesson','')).isdigit() else None; test=int(r['tests']) if str(r.get('tests','')).isdigit() else None; s=r['subject']
    try:
        if s=='math' and test: return {'assessmentFamily':math_assessment_family(test,r['entry_date'],set())}
        if s=='math' and lesson: return resolve_math_lesson(lesson)
        if s=='reading' and test: return {'assessmentFamily':reading_assessment_family(test,r['entry_date'])}
        if s=='reading' and lesson: return resolve_reading_lesson(lesson)
        if s=='spelling' and test: return resolve_spelling_test(test)
        if s in {'history','science'}: return {'assignmentPolicy':'disabled','reason':'owner-approved-subject-policy','agendaCapable':True}
    except Exception as e: return {'error':str(e)}
    return {'status':'unresolved'}
def collect_assessments_from_rows(rows,week_start):
    out=[]; seen=set()
    for r in rows:
        test=int(r['tests']) if str(r.get('tests','')).isdigit() else None; s=r['subject']; ed=r['entry_date']
        if s=='reading' and test:
            fam=reading_assessment_family(test,ed); key=fam['assessmentFamilyId']
            if key in seen: continue
            seen.add(key)
            bullet=f"Reading Test {test} on {weekday_for('',ed)} {ed}"
            if fam['checkout']:
                bullet=f"Reading Test {test} and Checkout {test} on {weekday_for('',ed)} {ed}"
            out.append({'date':ed,'familyId':key,'bullet':bullet,'studyGuides':[{'label':f'Reading Test {test} Study Guide','verifiedUrl':None}]})
        if s=='math' and test:
            key=f'math-{test}-{ed}'
            if key in seen: continue
            seen.add(key); out.append({'date':ed,'familyId':key,'bullet':f"Math Written Test {test} and Fact Test {test} on {weekday_for('',ed)} {ed}",'studyGuides':[{'label':f'Math Study Guide {test} Blank','verifiedUrl':None},{'label':f'Math Study Guide {test} Completed','verifiedUrl':None}]})
        if s=='spelling' and test:
            key=f'spell-{test}-{ed}'
            if key in seen: continue
            seen.add(key); out.append({'date':ed,'familyId':key,'bullet':f"Spelling Test {test} on {weekday_for('',ed)} {ed}",'studyGuides':[]})
    return out
def verified_link_html(label,url):
    if url and str(url).startswith('http') and '#' not in str(url) and not str(url).lower().startswith('javascript:'): return f'<li><a href="{html.escape(url)}">{html.escape(label)}</a></li>'
    return ''
def build_reminders_html(week_meta,assessments,resources,week_start):
    window_end=(date.fromisoformat(week_start)+timedelta(days=9)).isoformat() if week_start else None; items=[]; seen=set()
    for a in sorted(assessments,key=lambda x:x['date']):
        if window_end and not (week_start<=a['date']<=window_end): continue
        key=a.get('familyId') or a['bullet']
        if key in seen: continue
        seen.add(key); items.append(f'<li>{html.escape(a["bullet"])}</li>')
        for sg in a.get('studyGuides',[]):
            if sg.get('verifiedUrl'): items.append(verified_link_html(sg['label'],sg['verifiedUrl']))
    for res in resources or []:
        if res.get('verifiedUrl'): items.append(verified_link_html(res.get('label','Resource'),res['verifiedUrl']))
    if not items: items=['<li>&nbsp;</li>']
    return '<ul>'+''.join(items)+'</ul>'
def render_agenda_html(week_meta,rows,assessments=None,resources=None):
    iw=week_meta or {}; subtitle=iw.get('displaySubtitle') or f"Quarter {iw.get('quarter','?')}, Week {iw.get('week','?')}"
    week_start=iw.get('startsOn') or (rows[0]['entry_date'] if rows else ''); reminders=build_reminders_html(iw,assessments or collect_assessments_from_rows(rows,week_start),resources or [],week_start)
    parts=[f'<div id="kl_wrapper_3" class="kl_circle_left kl_wrapper" style="border-style: none;"><div id="kl_banner" class=""><p style="color: {WHITE}; background-color: {BLUE}; text-align: center; margin: 0;"><span style="font-size: 18pt;">&nbsp;Weekly Agenda</span><br><span style="font-size: 10pt;">{html.escape(subtitle)}</span></p><h3 style="background-color: {MAGENTA}; color: {WHITE}; border: 0 !important;">Reminders &amp; Resources</h3><div style="width: 100%; padding-left: 15px;">{reminders}</div>']
    for idx,wd in enumerate(WEEKDAYS):
        dr=[r for r in rows if r['weekday']==wd]; in_class=''.join(f'<li>{html.escape(x.get("in_class") or x.get("title") or " ")}</li>' for x in dr) or '<li>&nbsp;&nbsp;</li>'
        at_home_items=[x for x in dr if compact(x.get('at_home',''))]; show_at_home=wd!='Friday' or at_home_items; at_home=''.join(f'<li>{html.escape(x["at_home"])}</li>' for x in at_home_items) if at_home_items else '<li>&nbsp;&nbsp;</li>'
        parts.append(f'<div id="{DAY_BLOCK_IDS[idx]}" class=""><h3 style="color: {WHITE}; background-color: {BLUE}; margin-top: 15px; margin-bottom: 2px; border: 0 !important;">{wd}</h3><div style="display: flex; width: 100%;"><div style="width: 49%; padding-left: 15px;"><h4 class="kl_solid_border" style="color: {WHITE}; background-color: {DGRAY}; padding-left: 10px; margin: 0; border: 0 !important;">In Class</h4><ul>{in_class}</ul></div>')
        if show_at_home: parts.append(f'<div style="width: 49%; padding-left: 15px;"><h4 class="kl_solid_border" style="color: {WHITE}; background-color: {DGRAY}; padding-left: 10px; margin: 0; border: 0 !important;">At Home</h4><ul>{at_home}</ul></div>')
        parts.append('</div></div>')
    parts.append('</div></div>'); return ''.join(parts)
def assignment_drafts_for_day(r):
    s=r['subject']; lesson=int(r['lesson']) if str(r.get('lesson','')).isdigit() else None; test=int(r['tests']) if str(r.get('tests','')).isdigit() else None; out=[]
    if s in {'history','science'}: return []
    if s=='math' and test:
        fam=math_assessment_family(test,r['entry_date'],set()); out=[('assignment','math',f'SM5 Study Guide {test}',fam['suppressionReason']),('assignment','math',f'SM5 Written Test {test}','Local editable written test draft.'),('assignment','math',f'SM5 Fact Test {test}',fam['factTest']['practiceDescription'])]
    elif s=='math' and lesson and r['weekday']!='Friday': out=[('assignment','math',f"SM5 Lesson {lesson} {resolve_math_lesson(lesson)['suggestedHomework']}",'Local Odds/Evens homework draft. Due time unresolved.')]
    elif s=='reading' and test:
        fam=reading_assessment_family(test,r['entry_date']); out=[('assignment','reading',fam['readingTest']['title'],reading_test_description(test))]
        if fam['checkout']:
            out.append(('assignment','reading',fam['checkout']['title'],checkout_description(test)))
            out.append(('announcement','reading',f"Reading Test and Checkout - {r['entry_date']}",reading_announcement_body(fam)))
        else:
            out.append(('announcement','reading',f"Reading Test - {r['entry_date']}",reading_announcement_body(fam)))
    elif s=='spelling' and test: out=[('assignment','spelling',f'SPELL Test {test}','Focus words: '+', '.join(resolve_spelling_test(test)['focusWords']))]
    elif s=='language-arts' and (lesson or r['title']): out=[('assignment','language-arts',r['title'] or 'ELA4 practice','Local Language Arts draft.')]
    return out
def replace_drafts(db,wid):
    db.execute('DELETE FROM drafts WHERE weekly_plan_id=?',(wid,)); rows=[dict(r) for r in db.execute('SELECT * FROM daily_subject_entries WHERE weekly_plan_id=? ORDER BY entry_date,subject',(wid,))]
    plan=db.execute('SELECT payload,starts_on FROM weekly_plans WHERE id=?',(wid,)).fetchone(); payload=jl(plan['payload'],{}); iw=payload.get('instructionalWeek') or instructional_week_by_starts_on(plan['starts_on']) or {}
    groups={'math':['math'],'reading-spelling':['reading','spelling'],'language-arts':['language-arts'],'history':['history'],'science':['science']}
    for key,subs in groups.items():
        rs=[r for r in rows if r['subject'] in subs]
        if rs: insert_draft(db,wid,'page',key,f'{key} Agenda',f'{key} Agenda',render_agenda_html(iw,rs),{'subjects':subs,'instructionalWeek':iw})
    for r in rows:
        for kind,sub,title,text in assignment_drafts_for_day(r):
            extra={'unresolvedDueTime':True}
            if sub=='reading' and kind=='announcement': extra={'assessmentFamily':jl(r.get('resolver_output') or '{}',{}).get('assessmentFamily')}
            insert_draft(db,wid,kind,sub,title,text,f'<p>{html.escape(text)}</p>',extra)
    insert_draft(db,wid,'newsletter','homeroom','Newsletter Draft','Preview newsletter; unsent.','<p>Preview newsletter; unsent.</p>',{'previewOnly':True})
    insert_draft(db,wid,'announcement','all','Weekly Page Update','Preview announcement; unsent.','<p>Preview announcement; unsent.</p>',{'previewOnly':True})
    insert_draft(db,wid,'daily_brief','homeroom','Daily Teacher Brief','Recipient: owen.reagan@thalesacademy.org\nSchedule: 6:15 AM America/New_York instructional days\nWeather: placeholder only.\nClassroom-safe joke: Why did the notebook smile? It had good margins.','<pre>Recipient: owen.reagan@thalesacademy.org</pre>',{'previewOnly':True})
def insert_draft(db,wid,kind,sub,title,text,html_body,payload): db.execute('INSERT INTO drafts(id,weekly_plan_id,kind,subject,title,body_text,body_html,status,idempotency_key,payload,created_at,updated_at,updated_by) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',(stable_id('draft',wid,kind,sub,title),wid,kind,sub,title,text,html_body,'draft',stable_id('idem',wid,kind,sub,title),jd(payload),now_utc(),now_utc(),'generator'))
def replace_deployment(db,wid):
    db.execute('DELETE FROM deployment_items WHERE deployment_plan_id IN (SELECT id FROM deployment_plans WHERE weekly_plan_id=?)',(wid,)); db.execute('DELETE FROM deployment_plans WHERE weekly_plan_id=?',(wid,)); pid=stable_id('deployment',wid)
    db.execute('INSERT INTO deployment_plans(id,weekly_plan_id,status,payload,created_at,updated_at,updated_by) VALUES(?,?,?,?,?,?,?)',(pid,wid,'preview_only',jd({'previewOnly':True,'canvasWritesAllowed':False,'emailSendsAllowed':False,'scheduleIntent':'Friday 4:00 PM America/New_York','operations':['validate resources','create/update assignments','capture assignment URLs','render agenda pages with verified URLs','publish pages','set front pages','send page-update announcements','send assessment reminders','verify results']}),now_utc(),now_utc(),'generator'))
    for i,d in enumerate(db.execute('SELECT * FROM drafts WHERE weekly_plan_id=?',(wid,))):
        unresolved=['Teacher approval required']; payload=jl(d['payload'],{})
        if payload.get('unresolvedDueTime'): unresolved.append('Canvas assignment due time unresolved')
        db.execute('INSERT INTO deployment_items(id,deployment_plan_id,item_type,target,dependency_order,status,approved,validated,current_year_mapped,stale,already_deployed,unresolved_dependencies,idempotency_key,payload,created_at,updated_at,updated_by) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(stable_id('deploy-item',d['id']),pid,d['kind'],d['title'],i+1,'blocked_preview',0,0,1,0,0,jd(unresolved),stable_id('idem','deploy',d['id']),jd({'previewOnly':True}),now_utc(),now_utc(),'generator'))
def row_to_week(db,row):
    w=dict(row); w['deployment_status']=jl(w['deployment_status'],{}); w['payload']=jl(w['payload'],{}); w['subjects']=[]
    for s in db.execute('SELECT * FROM subject_weekly_plans WHERE weekly_plan_id=? ORDER BY subject',(row['id'],)):
        sd=dict(s); sd['payload']=jl(sd['payload'],{}); sd['days']=[]
        for d in db.execute('SELECT * FROM daily_subject_entries WHERE subject_plan_id=? ORDER BY entry_date',(s['id'],)):
            dd=dict(d); dd['resources']=jl(dd['resources'],[]); dd['resolver_output']=jl(dd['resolver_output'],{}); dd['validation']=jl(dd['validation'],[]); sd['days'].append(dd)
        w['subjects'].append(sd)
    w['drafts']=[dict(x) for x in db.execute('SELECT * FROM drafts WHERE weekly_plan_id=?',(row['id'],))]; w['deploymentPreview']=deployment_preview(db,row['id']); w['validation']=collect_validation(w); return w
def collect_validation(w):
    vals=[v for s in w.get('subjects',[]) for d in s.get('days',[]) for v in d.get('validation',[])]
    vals += [{'severity':'warning','message':'Canvas assignment due-time convention remains unresolved; no 12:00 AM or 11:59 PM guess is applied.'},{'severity':'pass','message':'Phase 22 is preview-only: no Canvas writes and no email sends.'}]; return vals
def deployment_preview(db,wid):
    p=db.execute('SELECT * FROM deployment_plans WHERE weekly_plan_id=?',(wid,)).fetchone()
    if not p: return None
    out=dict(p); out['payload']=jl(out['payload'],{}); out['items']=[]
    for r in db.execute('SELECT * FROM deployment_items WHERE deployment_plan_id=? ORDER BY dependency_order',(p['id'],)):
        d=dict(r); d['unresolved_dependencies']=jl(d['unresolved_dependencies'],[]); d['payload']=jl(d['payload'],{}); out['items'].append(d)
    return out
def build_payload(source,kind):
    source=Path(source)
    manifest_path=source.with_suffix('.manifest.json')
    if manifest_path.exists():
        source_manifest=json.loads(manifest_path.read_text())
        if source_manifest.get('artifactClassification') not in PHASE22_ARTIFACT_CLASSES: raise ValueError('phase 22 source manifest classification rejected')
        if source_manifest.get('containsStudentData') is not False: raise ValueError('phase 22 source manifest must declare containsStudentData false')
    g,r,e,u=import_pacing_grid(source,kind); payload={'phase':'22','product':'Predictive Weekly Planning Workstation','privacyBoundary':{'studentDataAllowed':False,'canvasWritesAllowed':False,'emailSendsAllowed':False,'rawSourceCommitted':False,'assessmentResultsExcluded':True},'yearlyPacingGuide':asdict(g),'importReport':asdict(r),'excludedCellReport':e,'unresolvedCellReport':u}
    payload['artifactClassification']='synthetic-curriculum'
    payload['containsStudentData']=False
    payload['sourceArtifact']={'path':safe_repo_relative(source),'classification':'synthetic-curriculum','containsStudentData':False}
    payload['importReport'].update({'artifactClassification':'teacher-planning','containsStudentData':False})
    if not no_sensitive_payload(payload): raise ValueError('Sensitive content detected')
    validation=phase22_validate_artifact_payload(payload,'phase22-demo')
    if not validation['safe']: raise ValueError('Phase 22 artifact classification gate failed')
    return payload
def write_json(path,payload): path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+'\n')
class Handler(SimpleHTTPRequestHandler):
    db_path=DEFAULT_DB_PATH
    def db(self): db=WorkstationDB(self.db_path); db.migrate(); db.seed_from_fixture(); return db
    def sendj(self,p,status=200):
        b=json.dumps(p,indent=2,ensure_ascii=False).encode(); self.send_response(status); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b)
    def body(self): return json.loads(self.rfile.read(int(self.headers.get('Content-Length','0') or 0)).decode() or '{}')
    def do_GET(self):
        u=urllib.parse.urlparse(self.path)
        if u.path.startswith('/api/'): return self.api('GET',u)
        if u.path=='/': self.path='/index.html'
        return SimpleHTTPRequestHandler.do_GET(self)
    def do_POST(self): return self.api('POST',urllib.parse.urlparse(self.path))
    def do_PATCH(self): return self.api('PATCH',urllib.parse.urlparse(self.path))
    def api(self,m,u):
        try:
            db=self.db(); path=u.path
            if m=='GET' and path=='/api/health': return self.sendj({'ok':True,'phase':22,'dbPath':str(db.path),'canvasWritesAllowed':False,'emailSendsAllowed':False})
            if m=='GET' and path=='/api/bootstrap': return self.sendj({'settings':default_settings(),'subjects':SUBJECTS,'currentWeek':db.current_week(),'weeklyStates':sorted(WEEKLY_STATES),'instructionalWeeks':load_instructional_weeks(),'weekCount':len(load_instructional_weeks())})
            if m=='GET' and path=='/api/settings': return self.sendj(default_settings())
            if m=='PATCH' and path=='/api/settings': return self.sendj({**default_settings(),**self.body()})
            if m=='GET' and path=='/api/calendar': return self.sendj({'timezone':'America/New_York','instructionalWeeks':load_instructional_weeks(),'weekCount':len(load_instructional_weeks()),'noSchoolDates':[]})
            if m=='GET' and path=='/api/calendar/instructional-weeks': return self.sendj({'weeks':load_instructional_weeks(),'weekCount':len(load_instructional_weeks()),'quarterWeekCounts':rjson('canvas/instructional-weeks-2026-2027.json')['quarterWeekCounts']})
            if m=='PATCH' and path=='/api/calendar': return self.sendj({'ok':True})
            if m=='POST' and path=='/api/pacing/import': return self.sendj(db.import_pacing(Path(self.body().get('source',RAW_IMPORT_PATH))))
            if m=='GET' and path=='/api/pacing':
                with db.connect() as c: return self.sendj({'entries':[dict(r) for r in c.execute('SELECT * FROM pacing_entries ORDER BY entry_date,subject LIMIT 1000')]})
            if m=='PATCH' and re.fullmatch(r'/api/pacing/[^/]+',path):
                b=self.body(); r=db.patch_table('pacing_entries',path.rsplit('/',1)[-1],b.get('fields',b),b.get('version')); return self.sendj(r,409 if r.get('conflict') else 200)
            if m=='GET' and path=='/api/weeks/current': return self.sendj(db.current_week())
            if m=='POST' and path=='/api/weeks': return self.sendj(db.get_week(db.create_week(self.body().get('startsOn','2026-08-17'))),201)
            if m=='GET' and re.fullmatch(r'/api/weeks/by-code/[^/]+',path):
                try: return self.sendj(db.get_week_by_code(urllib.parse.unquote(path.rsplit('/',1)[-1])))
                except KeyError: return self.sendj({'error':'week code not found'},404)
            if m=='GET' and re.fullmatch(r'/api/weeks/[^/]+',path): return self.sendj(db.get_week(path.rsplit('/',1)[-1]))
            if m=='PATCH' and re.fullmatch(r'/api/weeks/[^/]+',path):
                b=self.body(); r=db.patch_table('weekly_plans',path.rsplit('/',1)[-1],b.get('fields',b),b.get('version')); return self.sendj(r,409 if r.get('conflict') else 200)
            if m=='GET' and re.fullmatch(r'/api/weeks/[^/]+/subjects',path): return self.sendj(db.get_week(path.split('/')[3])['subjects'])
            if m=='PATCH' and re.fullmatch(r'/api/daily-entries/[^/]+',path):
                b=self.body(); r=db.patch_table('daily_subject_entries',path.rsplit('/',1)[-1],b.get('fields',b),b.get('version')); return self.sendj(r,409 if r.get('conflict') else 200)
            if m=='POST' and re.fullmatch(r'/api/weeks/[^/]+/generate',path): return self.sendj(db.generate_week(path.split('/')[3]))
            if m=='GET' and path=='/api/resources': return self.sendj({'resources':db.resources()})
            if m=='POST' and path=='/api/resources': return self.sendj(db.register_resource(self.body()),201)
            if m=='GET' and path=='/api/drafts':
                with db.connect() as c: return self.sendj({'drafts':[dict(r) for r in c.execute('SELECT * FROM drafts ORDER BY updated_at DESC LIMIT 300')]})
            if m=='GET' and re.fullmatch(r'/api/drafts/[^/]+',path):
                with db.connect() as c: row=c.execute('SELECT * FROM drafts WHERE id=?',(path.rsplit('/',1)[-1],)).fetchone(); return self.sendj(dict(row) if row else {'error':'not found'},200 if row else 404)
            if m=='PATCH' and re.fullmatch(r'/api/drafts/[^/]+',path):
                b=self.body(); r=db.patch_table('drafts',path.rsplit('/',1)[-1],b.get('fields',b),b.get('version')); return self.sendj(r,409 if r.get('conflict') else 200)
            if m=='POST' and re.fullmatch(r'/api/drafts/[^/]+/regenerate',path): return self.sendj(db.current_week()['week'])
            if m=='GET' and path=='/api/revisions': return self.sendj({'revisions':db.list_revisions()})
            if m=='POST' and re.fullmatch(r'/api/revisions/[^/]+/restore',path): return self.sendj(db.restore_revision(path.split('/')[3]))
            if m=='POST' and path=='/api/backups': return self.sendj({'backupPath':str(db.backup('manual'))})
            if m=='GET' and path=='/api/deployment-preview': return self.sendj(db.current_week()['week']['deploymentPreview'])
            if m=='GET' and re.fullmatch(r'/api/weeks/[^/]+/agenda-preview',path):
                wid=path.split('/')[3]; wk=db.get_week(wid); iw=wk.get('payload',{}).get('instructionalWeek') or instructional_week_by_starts_on(wk['starts_on']) or {}
                rs=[d for s in wk.get('subjects',[]) for d in s.get('days',[]) if s['subject'] in ('reading','spelling')]; html_body=render_agenda_html(iw,rs); return self.sendj({'html':html_body,'instructionalWeek':iw})
            if m=='GET' and path=='/api/daily-brief':
                with db.connect() as c: row=c.execute("SELECT * FROM drafts WHERE kind='daily_brief' ORDER BY updated_at DESC LIMIT 1").fetchone(); return self.sendj(dict(row) if row else {})
            return self.sendj({'error':'not found'},404)
        except Exception as e: return self.sendj({'error':str(e)},500)
def command_import(a): db=WorkstationDB(a.db); db.migrate(); res=db.import_pacing(Path(a.source)); write_json(LOCAL_ROOT/'sanitized-pacing-artifact.json',res); print(f"Phase 22 import complete: entries={res['importReport']['entriesImported']} excluded={res['importReport']['excludedCells']} unresolved={res['importReport']['unresolvedCells']}"); return 0
def command_build_demo(a):
    out=Path(getattr(a,'out',COMMITTED_DEMO_PATH))
    write_json(out,build_payload(SYNTHETIC_FIXTURE_PATH,'synthetic-fixture'))
    print(f'Phase 22 committed demo data rebuilt: {out}')
    return 0
def command_validate(a):
    bad=False
    for raw in a.paths:
        p=Path(raw)
        if not p.exists():
            print(f'FAIL missing artifact: {p}')
            bad=True
            continue
        if p.is_dir():
            report=phase22_safe_quarantine_summary(p)
            print(f"PASS quarantine report: classification={report['classification']} containsStudentData={report['containsStudentData']} manifests={report['manifestCount']} courseManifests={report['courseManifestCount']} safe={report['safe']}")
            bad=bad or not report['safe']
            continue
        txt=p.read_text()
        if txt.strip().startswith(('{','[')):
            payload=json.loads(txt)
            report=phase22_validate_artifact_payload(payload,p.name)
            status='PASS' if report['safe'] else 'FAIL'
            print(f"{status} artifact quarantine: classification={report['classification']} containsStudentData={report['containsStudentData']} issues={len(report['issues'])} path={p}")
            bad=bad or not report['safe']
        else:
            sens=contains_sensitive_content(txt)
            print(f"{'FAIL' if sens else 'PASS'} text scan: path={p.name} containsSensitive={sens}")
            bad=bad or sens
    return int(bad)
def command_init_db(a): db=WorkstationDB(a.db); db.migrate(); db.seed_from_fixture(); print(f'Initialized Phase 22 database: {db.path}'); return 0
def command_serve(a): db=WorkstationDB(a.db); db.migrate(); db.seed_from_fixture(); Handler.db_path=db.path; os.chdir(APP_DIR); srv=ThreadingHTTPServer((a.host,a.port),Handler); print(f'Phase 22 workstation serving at http://{a.host}:{a.port} db={db.path}'); srv.serve_forever()
def command_self_test(a):
    import tempfile; p=Path(tempfile.mkdtemp())/'w.sqlite3'; db=WorkstationDB(p); db.migrate(); db.seed_from_fixture()
    weeks=load_instructional_weeks(); assert len(weeks)==37; assert weeks[0]['code']=='Q1W1' and weeks[0]['startsOn']=='2026-07-20'; assert instructional_week_by_code('Q1W5')['startsOn']=='2026-08-17'
    assert canonical_week_code('Q1_W1')=='Q1W1'; assert canonical_week_code('q4-w10')=='Q4W10'
    assert resolve_reading_test(1)['lessonRange']=={'start':1,'end':10}; assert resolve_reading_test(10)['lessonRange']=={'start':91,'end':100}
    assert resolve_checkout(1)['fluency']=={'wpm':100,'maxErrors':2}; assert resolve_checkout(7)['fluency']=={'wpm':100,'maxErrors':2}
    assert resolve_checkout(8)['fluency']=={'wpm':115,'maxErrors':2}; assert resolve_checkout(10)['fluency']=={'wpm':115,'maxErrors':2}
    assert resolve_checkout(11)['fluency']=={'wpm':130,'maxErrors':2}; assert resolve_checkout(13)['fluency']=={'wpm':130,'maxErrors':2}
    assert resolve_checkout(2)['passage']=='The Field of Flowers'; assert resolve_checkout(13)['passage']=='The Prince with the Peasants'; assert resolve_checkout(2)['title']=='RM4: Checkout 2'
    fam=reading_assessment_family(2,'2026-07-21'); assert fam['assessmentFamilyId']; assert fam['sourceCheckoutKey']=='Check out 20'
    fam14=reading_assessment_family(14,'2026-07-21'); assert fam14['checkout'] is None and fam14['checkoutNumber'] is None and fam14['warnings']==[]; assert 'Checkout 14' not in reading_announcement_body(fam14); assert reading_checkout_number(14) is None
    assert resolve_math_lesson(1)['suggestedHomework']=='Odds'; assert resolve_fact_test(1)['powerUpCode']; assert resolve_reading_lesson(1)['page']==4
    w=db.current_week()['week']; d=w['subjects'][0]['days'][0]; up=db.patch_table('daily_subject_entries',d['id'],{'lesson':'1','title':'Lesson 1'},d['version'])
    assert up['version']==d['version']+1 and up['record']['title']=='Lesson 1'; assert db.patch_table('daily_subject_entries',d['id'],{'title':'stale'},d['version'])['status']==409
    by_code=db.get_week_by_code('Q1_W1'); assert by_code['id']==w['id']; demo=build_payload(SYNTHETIC_FIXTURE_PATH,'synthetic-fixture'); assert demo['artifactClassification']=='synthetic-curriculum' and demo['containsStudentData'] is False
    up2=db.patch_table('daily_subject_entries',d['id'],{'title':'Lesson 2'},up['version']); assert up2['title']=='Lesson 2'
    db2=WorkstationDB(p); got=db2.get_week(w['id']); assert got['subjects'][0]['days'][0]['title']=='Lesson 2'
    db.generate_week(w['id']); html=''.join(x['body_html'] for x in db.get_week(w['id'])['drafts'])
    assert 'kl_wrapper_3' in html and 'Reminders &amp; Resources' in html and 'display: flex' in html and 'width: 49%' in html and 'In Class' in html and 'At Home' in html
    assert 'href="#"' not in html; print('PASS Phase 22 self-test complete'); return 0
def command_runtime_proof(a):
    import tempfile,urllib.request,subprocess,time
    tmp=Path(tempfile.mkdtemp()); dbp=tmp/'proof.sqlite3'; db=WorkstationDB(dbp); db.migrate(); db.seed_from_fixture(); w=db.current_week()['week']; d=w['subjects'][0]['days'][0]
    port=a.port; env=os.environ.copy(); env['PHASE22_DB_PATH']=str(dbp); serve_cmd=[sys.executable,str(REPO_ROOT/'scripts/canvas_llm_phase22/phase22_workstation.py'),'--db',str(dbp),'serve','--host','127.0.0.1','--port',str(port)]; proc=subprocess.Popen(serve_cmd,cwd=APP_DIR,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        for _ in range(80):
            try: urllib.request.urlopen(f'http://127.0.0.1:{port}/api/health',timeout=1); break
            except Exception: time.sleep(0.25)
        else: raise RuntimeError('server failed to start')
        health=json.loads(urllib.request.urlopen(f'http://127.0.0.1:{port}/api/health').read()); assert health['canvasWritesAllowed'] is False and health['emailSendsAllowed'] is False
        boot=json.loads(urllib.request.urlopen(f'http://127.0.0.1:{port}/api/bootstrap').read())
        req=urllib.request.Request(f'http://127.0.0.1:{port}/api/daily-entries/{d["id"]}',data=json.dumps({'version':d['version'],'fields':{'title':'Runtime Proof 1'}}).encode(),headers={'Content-Type':'application/json'},method='PATCH')
        up1=json.loads(urllib.request.urlopen(req).read()); v1=up1['version']
        req2=urllib.request.Request(f'http://127.0.0.1:{port}/api/daily-entries/{d["id"]}',data=json.dumps({'version':v1,'fields':{'title':'Runtime Proof 2'}}).encode(),headers={'Content-Type':'application/json'},method='PATCH')
        up2=json.loads(urllib.request.urlopen(req2).read()); assert up2['title']=='Runtime Proof 2'
        stale=urllib.request.Request(f'http://127.0.0.1:{port}/api/daily-entries/{d["id"]}',data=json.dumps({'version':d['version'],'fields':{'title':'stale'}}).encode(),headers={'Content-Type':'application/json'},method='PATCH')
        try: urllib.request.urlopen(stale); raise AssertionError('stale allowed')
        except urllib.error.HTTPError as e: assert e.code==409
    finally:
        proc.terminate(); proc.wait(timeout=5)
    db3=WorkstationDB(dbp); got=db3.get_week(w['id']); assert got['subjects'][0]['days'][0]['title']=='Runtime Proof 2'
    db3.seed_from_fixture(); got2=db3.get_week(w['id']); assert got2['subjects'][0]['days'][0]['title']=='Runtime Proof 2'
    proc2=subprocess.Popen(serve_cmd,cwd=APP_DIR,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        for _ in range(80):
            try: urllib.request.urlopen(f'http://127.0.0.1:{port}/api/health',timeout=1); break
            except Exception: time.sleep(0.25)
        page=urllib.request.urlopen(f'http://127.0.0.1:{port}/').read().decode(); assert 'Predictive Weekly Planning' in page
        prev=json.loads(urllib.request.urlopen(f'http://127.0.0.1:{port}/api/weeks/{w["id"]}/agenda-preview').read()); assert 'Reminders &amp; Resources' in prev['html']
    finally: proc2.terminate(); proc2.wait(timeout=5)
    print('PASS Phase 22 runtime proof complete'); return 0
def command_browser_proof(a):
    import tempfile
    tmp=Path(tempfile.mkdtemp())
    dbp=tmp/'browser.sqlite3'
    profile=tmp/'chrome-profile'
    port=a.port
    probe=socket.socket(); probe.bind(('127.0.0.1',0)); debug_port=probe.getsockname()[1]; probe.close()
    env=os.environ.copy()
    env['PHASE22_DB_PATH']=str(dbp)
    serve_cmd=[sys.executable,str(REPO_ROOT/'scripts/canvas_llm_phase22/phase22_workstation.py'),'--db',str(dbp),'serve','--host','127.0.0.1','--port',str(port)]
    server=subprocess.Popen(serve_cmd,cwd=APP_DIR,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    chrome= subprocess.Popen([
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        '--headless=new',
        '--disable-gpu',
        '--no-first-run',
        '--no-default-browser-check',
        f'--user-data-dir={profile}',
        f'--remote-debugging-port={debug_port}',
        f'http://127.0.0.1:{port}/'
    ],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    cdp=None
    try:
        wait_for_http_json(f'http://127.0.0.1:{debug_port}/json/version')
        pages=wait_for_http_json(f'http://127.0.0.1:{debug_port}/json/list')
        ws_url=next(item['webSocketDebuggerUrl'] for item in pages if item.get('type')=='page')
        cdp=ChromeCDP(ws_url)
        cdp.call('Runtime.enable')
        cdp.call('Page.enable')
        wait_for_condition(cdp,"document.readyState === 'complete' && document.querySelectorAll('.week-chooser button[data-week-code]').length === 37")
        buttons=cdp.eval("Array.from(document.querySelectorAll('.week-chooser button[data-week-code]')).map((b) => b.dataset.weekCode)")
        assert len(buttons)==37 and len(set(buttons))==37
        for code in ['Q1W1','Q1W9','Q2W1','Q2W9','Q3W1','Q3W9','Q4W1','Q4W10']:
            assert code in buttons
        cdp.eval("window.__phase22FetchLog = []; window.__phase22OriginalFetch = window.fetch.bind(window); window.fetch = (...args) => { window.__phase22FetchLog.push(String(args[0])); return window.__phase22OriginalFetch(...args); };")
        cdp.eval("document.querySelector('[data-week-code=\"Q4W10\"]').click();")
        wait_for_condition(cdp,"document.querySelector('#week-code') && document.querySelector('#week-code').textContent === 'Q4W10'")
        assert cdp.eval(f"localStorage.getItem('{SELECTED_WEEK_STORAGE_KEY}')") == 'Q4W10'
        fetch_log=cdp.eval("window.__phase22FetchLog || []")
        assert any('/api/weeks/by-code/Q4W10' in str(item) for item in fetch_log)
        first_input=cdp.eval("(() => { const el = document.querySelector('#week-grid input[data-field=\"lesson\"]'); el.value = 'Browser Proof Lesson'; el.dispatchEvent(new Event('input', { bubbles: true })); return el.value; })()")
        assert first_input == 'Browser Proof Lesson'
        state_before=cdp.eval("document.querySelector('#save-state').textContent")
        assert state_before != 'Saved'
        wait_for_condition(cdp,"document.querySelector('#save-state') && document.querySelector('#save-state').textContent === 'Saved'")
        saved_value=cdp.eval("document.querySelector('#week-grid input[data-field=\"lesson\"]').value")
        assert saved_value == 'Browser Proof Lesson'
        cdp.call('Page.reload',{'ignoreCache':True})
        wait_for_condition(cdp,"document.querySelector('#week-grid input[data-field=\"lesson\"]') && document.querySelector('#week-grid input[data-field=\"lesson\"]').value === 'Browser Proof Lesson'")
        assert cdp.eval(f"localStorage.getItem('{SELECTED_WEEK_STORAGE_KEY}')") == 'Q4W10'
        server.terminate(); server.wait(timeout=5)
        server=subprocess.Popen(serve_cmd,cwd=APP_DIR,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        wait_for_http_json(f'http://127.0.0.1:{port}/api/health')
        cdp.call('Page.reload',{'ignoreCache':True})
        wait_for_condition(cdp,"document.querySelector('#week-grid input[data-field=\"lesson\"]') && document.querySelector('#week-grid input[data-field=\"lesson\"]').value === 'Browser Proof Lesson'")
        assert cdp.eval(f"localStorage.getItem('{SELECTED_WEEK_STORAGE_KEY}')") == 'Q4W10'
        assert cdp.eval("document.querySelector('#week-code').textContent") == 'Q4W10'
        assert cdp.eval("document.querySelector('#week-grid .subject-tab.active').dataset.subject")
        print('PASS Phase 22 browser proof complete')
        return 0
    finally:
        if cdp is not None:
            cdp.close()
        chrome.terminate()
        server.terminate()
        for proc in (chrome, server):
            try: proc.wait(timeout=5)
            except Exception: pass
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=os.environ.get('PHASE22_DB_PATH',str(DEFAULT_DB_PATH))); sub=ap.add_subparsers(dest='cmd',required=True)
    p=sub.add_parser('serve'); p.add_argument('--host',default='127.0.0.1'); p.add_argument('--port',type=int,default=8765); p.set_defaults(func=command_serve)
    sub.add_parser('init-db').set_defaults(func=command_init_db); p=sub.add_parser('import'); p.add_argument('--source',default=str(RAW_IMPORT_PATH)); p.set_defaults(func=command_import); p=sub.add_parser('build-demo'); p.add_argument('--out',default=str(COMMITTED_DEMO_PATH)); p.set_defaults(func=command_build_demo); p=sub.add_parser('validate-no-sensitive'); p.add_argument('paths',nargs='+'); p.set_defaults(func=command_validate); sub.add_parser('self-test').set_defaults(func=command_self_test); p=sub.add_parser('runtime-proof'); p.add_argument('--port',type=int,default=18765); p.set_defaults(func=command_runtime_proof); p=sub.add_parser('browser-proof'); p.add_argument('--port',type=int,default=18767); p.set_defaults(func=command_browser_proof)
    a=ap.parse_args(argv); return a.func(a)
if __name__=='__main__': raise SystemExit(main())
