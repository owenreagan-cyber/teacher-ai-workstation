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
    return {'testNumber':n,'title':f'RM4: Mastery Test {n}','lessonRange':{'start':start,'end':end},'assignmentGroup':'Tests/Assessments','points':100,'gradeDisplay':'Percentage','submissionType':'On Paper','assignedTo':'All Students','dueTime':'11:59 PM','timezone':'America/New_York'}
def resolve_checkout(n:int):
    if not 1<=n<=13: raise ValueError('Checkout number must be 1-13')
    m=rjson('reading/reading-mastery-4/checkout-passage-map.json')['checkouts'][str(n)]; flu=CHECKOUT_FLUENCY_CONFIRMED.get(str(n),{})
    return {'checkoutNumber':n,'readingTestNumber':n,'title':f'RM4: Fluency Checkout {n}','sourceCheckoutKey':m['sourceCheckoutKey'],'passage':m['passage'],'bookVolume':m['bookVolume'],'page':m['page'],'fluency':flu,'assignmentGroup':'Checkouts','points':100,'gradeDisplay':'Percentage','submissionType':'On Paper','assignedTo':'All Students','dueTime':'11:59 PM','timezone':'America/New_York','checkoutStudyGuideAllowed':False}
def reading_checkout_number(n:int):
    return n if 1<=n<=13 else None
def reading_test_description(test_num:int,has_study_guide=False):
    rt=resolve_reading_test(test_num); lr=rt['lessonRange']
    return f"Review Lessons {lr['start']}-{lr['end']}, including vocabulary and story details."
def checkout_description(n:int):
    return FLUENCY_PRACTICE_GENERIC
def reading_assessment_family(n:int,test_day:str):
    fid=stable_id('reading-assessment-family',n,test_day); rt=resolve_reading_test(n); checkout_number=reading_checkout_number(n); co=resolve_checkout(n) if checkout_number else None
    warnings=[]
    if co and not co['fluency'].get('wpm'): warnings.append(f"Checkout {n} WPM target unresolved; owner source required.")
    if co and co['fluency'].get('maxErrors') is None and str(n) not in CHECKOUT_FLUENCY_CONFIRMED: warnings.append(f"Checkout {n} maximum-error target unresolved.")
    return {'assessmentFamilyId':fid,'readingTestNumber':n,'checkoutNumber':checkout_number,'writtenTestDate':test_day,'checkoutDate':test_day if co else None,'readingTest':rt,'checkout':co,'announcementDraft':stable_id('reading-test-announcement',fid),'sourceCheckoutKey':co['sourceCheckoutKey'] if co else None,'checkoutStudyGuideAllowed':False,'warnings':warnings}
def reading_announcement_body(fam,has_study_guide=False):
    rt,co=fam['readingTest'],fam['checkout']; lr=rt['lessonRange']; lines=['Hello Families,',f"Assessment date: {fam['writtenTestDate']}",f"Reading Mastery Test {rt['testNumber']} covers Lessons {lr['start']}-{lr['end']}.", 'Review vocabulary and story details.']
    if co: lines.append(FLUENCY_PRACTICE_GENERIC)
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
_quarter_activation_cache=None
FLUENCY_PRACTICE_GENERIC='Have your child continue to practice fluency by reading a short paragraph of about 100 words aloud in less than one minute. They should make no more than 2 errors.'
ANNOUNCEMENT_SCHEDULE_DAY='Friday'
ANNOUNCEMENT_SCHEDULE_TIME='4:00 PM'
ANNOUNCEMENT_TIMEZONE='America/New_York'
ANNOUNCEMENT_SCHEDULE_INTENT='Friday 4:00 PM America/New_York'
CANONICAL_ASSESSMENT_TITLE_RE=re.compile(r'^(SM5|RM4|ELA4|HIST4|SCI4):',re.I)
FORBIDDEN_ANNOUNCEMENT_PATTERNS=(
    ('study guide','Study Guide language is forbidden in announcement drafts'),
    ('answer key','Answer key language is forbidden in announcement drafts'),
    ('focus words','Focus Words language is forbidden in announcement drafts'),
    ('sourcecheckoutkey','Checkout source key is forbidden in announcement drafts'),
    ('bookvolume','Book volume reference is forbidden in announcement drafts'),
)
def format_announcement_display_date(entry_date):
    d=date.fromisoformat(entry_date)
    return f"{d.strftime('%A')}, {d.strftime('%B')} {d.day}"
def is_canonical_assessment_title(title):
    return bool(CANONICAL_ASSESSMENT_TITLE_RE.match(compact(title)))
def sanitize_announcement_text(text):
    cleaned=compact(text or '')
    if not cleaned: return ''
    for needle,_ in FORBIDDEN_ANNOUNCEMENT_PATTERNS:
        if needle in cleaned.lower(): return ''
    if re.search(r'https?://',cleaned,re.I) or '<a ' in cleaned.lower() or 'href=' in cleaned.lower(): return ''
    return cleaned
def extract_teacher_coverage(row):
    ro=jl(row.get('resolver_output') or '{}',{})
    for key in ('announcementCoverage','coverage'):
        val=sanitize_announcement_text(ro.get(key) or row.get(key) or '')
        if val: return val
    topic=sanitize_announcement_text(ro.get('topic') or row.get('topic') or '')
    if topic and not is_canonical_assessment_title(topic): return topic
    title=sanitize_announcement_text(row.get('title') or '')
    if title and not is_canonical_assessment_title(title) and str(row.get('tests','')).isdigit(): return title
    if ro.get('announcementNoteSafe') and compact(row.get('notes') or ''): return sanitize_announcement_text(row.get('notes'))
    return ''
def fluency_practice_guidance(checkout_number):
    flu=CHECKOUT_FLUENCY_CONFIRMED.get(str(checkout_number),{'wpm':100,'maxErrors':2})
    wpm=flu.get('wpm') or 100
    return f'Students should practice reading approximately {wpm} words in under one minute with no more than two errors.'
def spelling_practice_guidance(test_number):
    practice_start=max(1,int(test_number)-4); practice_end=int(test_number)-1
    return f'For Spelling Test {test_number}, students should practice lessons {practice_start} through {practice_end}.'
def announcement_stable_id(week_code,subject,assessment_type,assessment_number,assessment_date):
    return stable_id('announcement-draft',week_code,subject,assessment_type,assessment_number,assessment_date)
def default_announcement_safety_metadata(**overrides):
    base={'canvasWritesAllowed':False,'emailSendsAllowed':False,'containsStudentData':False,'containsLinks':False,'containsAttachments':False,'containsExactSpellingWords':False,'containsExactCheckoutLocation':False,'studyGuideAllowed':False}
    base.update(overrides or {}); return base
def announcement_body_html(body_text):
    parts=[]
    for para in compact(body_text or '').split('\n'):
        if para: parts.append(f'<p>{html.escape(para)}</p>')
    return ''.join(parts) or '<p></p>'
def validate_announcement_safety(draft):
    blob=' '.join([draft.get('title') or '',draft.get('body_text') or '',draft.get('coverage') or '']).lower(); warnings=[]
    for needle,msg in FORBIDDEN_ANNOUNCEMENT_PATTERNS:
        if needle in blob: warnings.append(msg)
    if re.search(r'https?://',blob) or '<a ' in blob or 'href=' in blob: warnings.append('Links are forbidden in announcement drafts')
    if re.search(r'\bpage\s+\d+\b',blob) and 'checkout' in blob: warnings.append('Exact checkout page reference is forbidden in announcement drafts')
    if contains_sensitive_content(blob): warnings.append('Student-sensitive language is forbidden in announcement drafts')
    return warnings
def announcement_date_for_target_week(target_week_starts_on):
    starts_on=compact(target_week_starts_on or '')
    if not starts_on: return ''
    monday=date.fromisoformat(starts_on)
    if monday.weekday()!=0: return ''
    return (monday-timedelta(days=3)).isoformat()
def build_announcement_schedule_metadata(week_meta=None,overrides=None):
    week_meta=week_meta or {}; overrides=overrides or {}
    week_code=canonical_week_code(week_meta.get('code') or '')
    starts_on=week_meta.get('startsOn') or week_meta.get('starts_on') or ''
    if not starts_on and week_code:
        iw=instructional_week_by_code(week_code) or {}
        starts_on=iw.get('startsOn') or ''
    announcement_date=''; schedule_warnings=[]
    if starts_on: announcement_date=announcement_date_for_target_week(starts_on)
    teacher_override_applied=bool(compact(overrides.get('announcementScheduleDay') or '') or compact(overrides.get('announcementDate') or ''))
    override_date=compact(overrides.get('announcementDate') or '')
    if teacher_override_applied and override_date: announcement_date=override_date
    closed_dates=set(compact(d or '') for d in (week_meta.get('closedAnnouncementDates') or week_meta.get('noSchoolDates') or []) if compact(d or ''))
    if announcement_date and announcement_date in closed_dates and not teacher_override_applied:
        schedule_warnings.append('Preceding Friday announcement scheduling is unavailable due to calendar disruption; Friday 4:00 PM intent preserved for teacher review.')
    schedule={'scheduledDay':ANNOUNCEMENT_SCHEDULE_DAY,'scheduledTime':ANNOUNCEMENT_SCHEDULE_TIME,'timezone':ANNOUNCEMENT_TIMEZONE,'scheduleIntent':ANNOUNCEMENT_SCHEDULE_INTENT,'targetWeekCode':week_code,'targetWeekStartsOn':starts_on,'announcementDate':announcement_date,'teacherOverrideApplied':teacher_override_applied,'teacherApprovalRequired':True,'previewOnly':True,'canvasWritesAllowed':False,'emailSendsAllowed':False}
    return schedule,schedule_warnings
def build_week_announcement_drafts(rows,week_meta=None):
    if not rows: return []
    week_meta=week_meta or {}; week_code=canonical_week_code(week_meta.get('code') or '')
    ctx=build_week_graded_selection_context(rows,week_meta); window_findings=ctx.get('assessmentWindowValidation') or []
    overrides=dict((week_meta or {}).get('announcementScheduleOverrides') or {})
    for r in rows or []:
        ro=jl(r.get('resolver_output') or '{}',{}); sel=ro.get('announcementScheduleOverride') or {}
        if sel.get('announcementDate'): overrides['announcementDate']=compact(sel.get('announcementDate'))
        if sel.get('scheduledDay'): overrides['announcementScheduleDay']=compact(sel.get('scheduledDay'))
    schedule_metadata,schedule_warnings=build_announcement_schedule_metadata(week_meta,overrides)
    drafts=[]; seen=set()
    def window_warnings_for(subject,assessment_number):
        out=[]
        for finding in window_findings:
            if finding.get('severity')!='warn': continue
            target=compact(finding.get('target') or '')
            if subject=='math' and target in {f'math-test-{assessment_number}',f'math-fact-{assessment_number}'}: out.append(finding.get('message') or '')
            elif subject=='reading' and target in {f'reading-test-{assessment_number}',f'reading-checkout-{assessment_number}'}: out.append(finding.get('message') or '')
            elif subject=='spelling' and target==f'spelling-test-{assessment_number}': out.append(finding.get('message') or '')
            elif subject in {'history','science','language-arts','shurley'} and target.endswith(str(assessment_number)): out.append(finding.get('message') or '')
        return out
    def append_draft(*,subject,assessment_type,assessment_number,row,title,body_lines,generation_reason):
        key=(subject,assessment_type,assessment_number,row.get('entry_date'))
        if key in seen: return
        seen.add(key)
        coverage=extract_teacher_coverage(row); coverage_status='provided' if coverage else 'missing'
        warnings=list(schedule_warnings); needs_review=False
        if coverage_status=='missing':
            warnings.append('Teacher-entered coverage is required before approval'); needs_review=True
        warnings.extend(window_warnings_for(subject,assessment_number))
        if any(window_warnings_for(subject,assessment_number)): needs_review=True
        body_text='\n'.join([line for line in body_lines if compact(line)])
        if coverage: body_text=f"{body_text}\nCoverage: {coverage}."
        safety_warnings=validate_announcement_safety({'title':title,'body_text':body_text,'coverage':coverage}); warnings.extend(safety_warnings)
        if safety_warnings: needs_review=True
        draft={'announcement_id':announcement_stable_id(week_code,subject,assessment_type,assessment_number,row.get('entry_date')),'subject':subject,'title':title,'body_text':body_text,'body_html':announcement_body_html(body_text),'assessment_type':assessment_type,'assessment_number':assessment_number,'assessment_date':row.get('entry_date'),'display_date':format_announcement_display_date(row.get('entry_date')),'target_week_code':week_code,'coverage':coverage or None,'coverage_status':coverage_status,'schedule_metadata':dict(schedule_metadata),'approval_state':'Draft','needs_review':needs_review,'warnings':list(dict.fromkeys(warnings)),'provenance':[{'sourceType':'weekly-row','sourceRef':row.get('entry_date') or '','details':generation_reason},{'sourceType':'phase22-rule','sourceRef':'build_week_announcement_drafts','details':'explicit assessment event'}],'safety_metadata':default_announcement_safety_metadata(),'teacherApprovalRequired':True,'approved':False,'previewOnly':True,'generation_reason':generation_reason}
        drafts.append(draft)
    for r in rows:
        if not subject_active_for_quarter(r.get('subject'),week_meta): continue
        s=compact(r.get('subject')).lower(); test=int(r['tests']) if str(r.get('tests','')).isdigit() else None
        if not test: continue
        display_date=format_announcement_display_date(r['entry_date'])
        if s=='math':
            append_draft(subject='math',assessment_type='written_assessment',assessment_number=test,row=r,title=f'SM5: Written Assessment {test}',body_lines=[f'Math Written Assessment {test} is scheduled for {display_date}.','Students should review recent classwork and assigned practice.'],generation_reason='scheduled-written-assessment')
            fact=math_assessment_family(test,r['entry_date'],set())['factTest']; fact_lines=[f'Math Fact Assessment {test} is scheduled for {display_date}.']
            topic=sanitize_announcement_text(fact.get('practiceDescription') or '')
            if topic and 'worksheet' not in topic.lower() and 'http' not in topic.lower(): fact_lines.append(topic)
            append_draft(subject='math',assessment_type='fact_assessment',assessment_number=test,row=r,title=f'SM5: Fact Assessment {test}',body_lines=fact_lines,generation_reason='scheduled-fact-assessment')
        elif s=='reading':
            append_draft(subject='reading',assessment_type='mastery_test',assessment_number=test,row=r,title=f'RM4: Mastery Test {test}',body_lines=[f'Reading Mastery Test {test} is scheduled for {display_date}.'],generation_reason='scheduled-mastery-test')
            if reading_checkout_number(test):
                append_draft(subject='reading',assessment_type='fluency_checkout',assessment_number=test,row=r,title=f'RM4: Fluency Checkout {test}',body_lines=[f'Reading Fluency Checkout {test} is scheduled for {display_date}.',fluency_practice_guidance(test)],generation_reason='scheduled-fluency-checkout')
        elif s=='spelling':
            append_draft(subject='spelling',assessment_type='spelling_test',assessment_number=test,row=r,title=f'RM4: Spelling Test {test}',body_lines=[f'Spelling Test {test} is scheduled for {display_date}.',spelling_practice_guidance(test)],generation_reason='scheduled-spelling-test')
        elif s in {'language-arts','shurley'}:
            title=compact(r.get('title') or f'ELA4: Assessment {test}')
            if not title.startswith('ELA4:'): title=f'ELA4: {title}'
            append_draft(subject='language-arts',assessment_type='shurley_assessment',assessment_number=test,row=r,title=title,body_lines=[f'The Language Arts assessment is scheduled for {display_date}.'],generation_reason='scheduled-language-arts-assessment')
        elif s=='history':
            title=compact(r.get('title') or f'HIST4: Assessment {test}')
            if not title.startswith('HIST4:'): title=f'HIST4: Assessment {test}'
            append_draft(subject='history',assessment_type='history_assessment',assessment_number=test,row=r,title=title,body_lines=[f'The History assessment is scheduled for {display_date}.'],generation_reason='scheduled-history-assessment')
        elif s=='science':
            title=compact(r.get('title') or f'SCI4: Assessment {test}')
            if not title.startswith('SCI4:'): title=f'SCI4: Assessment {test}'
            append_draft(subject='science',assessment_type='science_assessment',assessment_number=test,row=r,title=title,body_lines=[f'The Science assessment is scheduled for {display_date}.'],generation_reason='scheduled-science-assessment')
    return drafts
NEWSLETTER_SECTION_ORDER=('Important Dates','Homeroom News','School News','School Information and Event Links')
HOMEROOM_NEWSLETTER_SUBJECT='homeroom'
HOMEROOM_NEWSLETTER_COURSE_ID=26427
FORBIDDEN_NEWSLETTER_PATTERNS=(
    ('study guide','Study Guide language is forbidden in newsletter drafts'),
    ('workbook','Workbook language is forbidden in newsletter drafts'),
    ('worksheet','Worksheet language is forbidden in newsletter drafts'),
    ('answer key','Answer key language is forbidden in newsletter drafts'),
    ('glossary','Glossary language is forbidden in newsletter drafts'),
    ('checkout 14','Checkout 14 wording is forbidden in newsletter drafts'),
    ('spelling test 25','Spelling Test 25 is forbidden until approved source data exists'),
)
def homeroom_newsletter_course_id():
    try: return int(resolve_course('2026-2027','production',HOMEROOM_NEWSLETTER_SUBJECT)['courseId'])
    except Exception: return HOMEROOM_NEWSLETTER_COURSE_ID
def month_code_for_date(value):
    d=date.fromisoformat(value) if isinstance(value,str) else value
    return f'{d.year}-{d.month:02d}'
def month_bounds(month_code):
    y,m=map(int,month_code.split('-')); start=date(y,m,1); end=date(y+1,1,1)-timedelta(days=1) if m==12 else date(y,m+1,1)-timedelta(days=1)
    return start.isoformat(),end.isoformat(),start.strftime('%B %Y')
def newsletter_title(month_label): return f'Homeroom Newsletter — {month_label}'
def newsletter_update_title(month_label): return f'Homeroom Newsletter Updated — {month_label}'
def newsletter_update_body(month_label): return f'The newsletter has been updated for {month_label}.'
def format_newsletter_display_date(entry_date):
    d=date.fromisoformat(entry_date); return f'{d.strftime("%B")} {d.day}, {d.year}'
def default_newsletter_month_state(month_code,school_year='2026-2027'):
    month_start,month_end,month_label=month_bounds(month_code)
    state={'month_code':month_code,'month_label':month_label,'school_year':school_year,'month_start':month_start,'month_end':month_end,'important_dates':[],'homeroom_news':[],'school_news':[],'school_links':[],'source_entry_ids':[],'source_revisions':[],'verified_page_url':None,'updated_at':'2026-07-11T00:00:00Z','updated_by':'generator'}
    if month_code=='2026-08':
        state['important_dates']=[{'label':'First Day of School','date':'2026-08-17'},{'label':'Curriculum Night','date':'2026-08-27'}]
        state['homeroom_news']=['Welcome to fourth grade.','Students will practice classroom routines and organization during the opening weeks.']
        state['school_news']=['Families should review current school arrival and dismissal procedures.','Please check official school communications for event updates.']
    return state
def normalize_newsletter_month_state(state):
    month_code=compact(state.get('month_code') or ''); school_year=compact(state.get('school_year') or '2026-2027'); month_start,month_end,month_label=month_bounds(month_code)
    links=[]
    for item in state.get('school_links') or []:
        if not isinstance(item,dict): continue
        label=compact(item.get('label') or ''); url=compact(item.get('url') or '')
        if label or url: links.append({'label':label,'url':url})
    return {'month_code':month_code,'month_label':compact(state.get('month_label') or month_label),'school_year':school_year,'month_start':compact(state.get('month_start') or month_start),'month_end':compact(state.get('month_end') or month_end),'important_dates':list(state.get('important_dates') or []),'homeroom_news':[compact(x) for x in (state.get('homeroom_news') or []) if compact(x)],'school_news':[compact(x) for x in (state.get('school_news') or []) if compact(x)],'school_links':links,'source_entry_ids':list(state.get('source_entry_ids') or []),'source_revisions':list(state.get('source_revisions') or []),'verified_page_url':state.get('verified_page_url'),'updated_at':compact(state.get('updated_at') or '2026-07-11T00:00:00Z'),'updated_by':compact(state.get('updated_by') or 'generator')}
def newsletter_stable_id(month_code,school_year='2026-2027'): return stable_id('newsletter-page',school_year,month_code)
def newsletter_update_stable_id(month_code,school_year='2026-2027'): return stable_id('newsletter-update',school_year,month_code)
def newsletter_content_hash(state):
    canonical=normalize_newsletter_month_state(state); canonical.pop('updated_at',None); canonical.pop('updated_by',None); canonical.pop('verified_page_url',None)
    return hashlib.sha256(jd(canonical).encode()).hexdigest()[:16]
def validate_newsletter_school_link(url):
    cleaned=compact(url or ''); lower=cleaned.lower()
    if not cleaned: return True
    if 'thales' in lower or 'instructure' in lower or 'javascript:' in lower: return False
    if any(x in lower for x in ('workbook','worksheet','textbook','study-guide','answer-key','glossary')): return False
    return lower.startswith('https://example.com') or lower.startswith('http://example.com')
def scan_newsletter_content_warnings(state):
    warnings=[]; blob=jd(normalize_newsletter_month_state(state)).lower()
    for needle,message in FORBIDDEN_NEWSLETTER_PATTERNS:
        if needle in blob: warnings.append(message)
    for link in state.get('school_links') or []:
        if not validate_newsletter_school_link((link or {}).get('url')): warnings.append('School/event link rejected; only approved example.com links are allowed in preview fixtures.')
    if not compact(state.get('verified_page_url') or ''): warnings.append('Newsletter publication timing remains teacher-selected; preview-only generation only.')
    return list(dict.fromkeys(warnings))
def build_newsletter_sections(state):
    normalized=normalize_newsletter_month_state(state); sections=[]
    important=[f"{item['label']} — {format_newsletter_display_date(item['date'])}" for item in normalized['important_dates'] if item.get('label') and item.get('date')]
    sections.append({'name':'Important Dates','items':important})
    sections.append({'name':'Homeroom News','items':list(normalized['homeroom_news'])})
    sections.append({'name':'School News','items':list(normalized['school_news'])})
    link_items=[]
    for link in normalized['school_links']:
        label=compact(link.get('label') or ''); url=compact(link.get('url') or '')
        if label and url and validate_newsletter_school_link(url): link_items.append({'label':label,'url':url})
    sections.append({'name':'School Information and Event Links','items':link_items})
    return sections
def render_newsletter_text(state):
    normalized=normalize_newsletter_month_state(state); parts=[newsletter_title(normalized['month_label']),'']
    for section in build_newsletter_sections(normalized):
        parts.append(section['name'])
        if section['name']=='School Information and Event Links':
            if section['items']:
                for item in section['items']: parts.append(f"- {item['label']}: {item['url']}")
            else: parts.append('-')
        else:
            for line in section['items']: parts.append(f'- {line}')
        parts.append('')
    return '\n'.join(parts).strip()
def render_newsletter_html(state):
    normalized=normalize_newsletter_month_state(state); parts=[f'<h1>{html.escape(newsletter_title(normalized["month_label"]))}</h1>']
    for section in build_newsletter_sections(normalized):
        parts.append(f'<h2>{html.escape(section["name"])}</h2><ul>')
        if section['name']=='School Information and Event Links':
            if section['items']:
                for item in section['items']: parts.append(f'<li><a href="{html.escape(item["url"])}">{html.escape(item["label"])}</a></li>')
            else: parts.append('<li>&nbsp;</li>')
        else:
            for line in section['items']: parts.append(f'<li>{html.escape(line)}</li>')
            if not section['items']: parts.append('<li>&nbsp;</li>')
        parts.append('</ul>')
    return ''.join(parts)
def build_monthly_newsletter_draft(state,week_code=None):
    normalized=normalize_newsletter_month_state(state); content_hash=newsletter_content_hash(normalized); warnings=scan_newsletter_content_warnings(normalized); local_object_id=newsletter_stable_id(normalized['month_code'],normalized['school_year'])
    return {'local_object_id':local_object_id,'month_code':normalized['month_code'],'month_label':normalized['month_label'],'school_year':normalized['school_year'],'course_id':homeroom_newsletter_course_id(),'title':newsletter_title(normalized['month_label']),'date_range':{'start':normalized['month_start'],'end':normalized['month_end']},'body_text':render_newsletter_text(normalized),'body_html':render_newsletter_html(normalized),'sections':build_newsletter_sections(normalized),'source_entry_ids':list(normalized['source_entry_ids']),'source_revisions':list(normalized['source_revisions']),'content_hash':content_hash,'dependencies':[],'blockers':[],'approval_state':'Draft','approval_revision':0,'snapshot_id':stable_id('newsletter-snapshot',content_hash),'deployment_status':'preview_only','verification_status':'unverified','preview_only':True,'teacher_approval_required':True,'approved':False,'canvas_writes_allowed':False,'email_sends_allowed':False,'subject':HOMEROOM_NEWSLETTER_SUBJECT,'artifact_kind':'newsletter','cadence':'monthly','generation_reason':'monthly-homeroom-newsletter','provenance':[{'sourceType':'monthly-state','sourceRef':normalized['month_code'],'details':'structured homeroom newsletter month state'}],'safety_metadata':{'canvasWritesAllowed':False,'emailSendsAllowed':False,'previewOnly':True,'containsStudentData':False,'schoolLinksAllowed':True,'curriculumResourceLinksAllowed':False},'needs_review':bool(warnings),'warnings':warnings,'resolved_week_code':week_code,'verified_page_url':normalized.get('verified_page_url')}
def build_newsletter_update_announcement(newsletter_draft):
    month_code=newsletter_draft['month_code']; month_label=newsletter_draft['month_label']; body_text=newsletter_update_body(month_label); page_url=newsletter_draft.get('verified_page_url'); verified=bool(compact(page_url or ''))
    blockers=['Newsletter page has not been created and verified.','Verified newsletter page URL is required.','Separate teacher approval is required.']
    if verified: blockers=[item for item in blockers if 'URL is required' not in item]
    return {'announcement_id':newsletter_update_stable_id(month_code,newsletter_draft['school_year']),'local_object_id':newsletter_update_stable_id(month_code,newsletter_draft['school_year']),'artifact_kind':'newsletter_update','logical_type':'newsletter_update','subject':HOMEROOM_NEWSLETTER_SUBJECT,'month_code':month_code,'month_label':month_label,'title':newsletter_update_title(month_label),'body_text':body_text,'body_html':f'<p>{html.escape(body_text)}</p>','depends_on':newsletter_draft['local_object_id'],'dependencies':[{'type':'newsletter_page','local_object_id':newsletter_draft['local_object_id'],'verification_status':'verified' if verified else 'unverified'}],'page_url':page_url if verified else None,'blockers':blockers,'approval_state':'Draft','approval_revision':0,'approved':False,'teacher_approval_required':True,'preview_only':True,'canvas_writes_allowed':False,'email_sends_allowed':False,'verification_status':'verified' if verified else 'unverified','deployment_status':'blocked_preview','needs_review':True,'schedule_metadata':None,'warnings':['Newsletter update announcement publication timing remains unresolved.'],'safety_metadata':{'canvasWritesAllowed':False,'emailSendsAllowed':False,'previewOnly':True,'containsStudentData':False},'content_hash':hashlib.sha256(body_text.encode()).hexdigest()[:16],'generation_reason':'newsletter-update-preview'}
def upsert_newsletter_month_state(db,state):
    normalized=normalize_newsletter_month_state(state); rid=stable_id('newsletter-month',normalized['school_year'],normalized['month_code'])
    db.execute('INSERT OR REPLACE INTO homeroom_newsletter_months(id,month_code,school_year,month_label,month_start,month_end,payload,version,created_at,updated_at,updated_by) VALUES(?,?,?,?,?,?,?,COALESCE((SELECT version FROM homeroom_newsletter_months WHERE month_code=? AND school_year=?),0)+1,COALESCE((SELECT created_at FROM homeroom_newsletter_months WHERE month_code=? AND school_year=?),?),?,?)',(rid,normalized['month_code'],normalized['school_year'],normalized['month_label'],normalized['month_start'],normalized['month_end'],jd(normalized),normalized['month_code'],normalized['school_year'],normalized['month_code'],normalized['school_year'],now_utc(),now_utc(),normalized['updated_by']))
    return normalized
def get_newsletter_month_state(db,month_code,school_year='2026-2027'):
    row=db.execute('SELECT payload FROM homeroom_newsletter_months WHERE month_code=? AND school_year=?',(month_code,school_year)).fetchone()
    if row: return normalize_newsletter_month_state(jl(row['payload'],{}))
    return upsert_newsletter_month_state(db,default_newsletter_month_state(month_code,school_year))
def resolve_newsletter_for_week_start(starts_on,db=None,school_year='2026-2027',week_code=None):
    month_code=month_code_for_date(starts_on); state=get_newsletter_month_state(db,month_code,school_year) if db is not None else normalize_newsletter_month_state(default_newsletter_month_state(month_code,school_year))
    newsletter=build_monthly_newsletter_draft(state,week_code=week_code); update=build_newsletter_update_announcement(newsletter); return state,newsletter,update
def load_quarter_subject_activation():
    global _quarter_activation_cache
    if not _quarter_activation_cache: _quarter_activation_cache=rjson('canvas/quarter-subject-activation-2026-2027.json')
    return _quarter_activation_cache
def quarter_key_from_week_meta(week_meta):
    if not week_meta: return None
    q=week_meta.get('quarter')
    if q: return f'Q{q}'
    m=re.match(r'Q([1-4])',compact(week_meta.get('code','')),re.I)
    return f'Q{m.group(1)}' if m else None
def subject_active_for_quarter(subject,week_meta):
    subject=compact(subject).lower()
    if subject not in {'history','science'}: return True
    qk=quarter_key_from_week_meta(week_meta)
    if not qk: return True
    activation=load_quarter_subject_activation()['quarters'].get(qk,{})
    return activation.get('activeSubject')==subject
def math_homework_for_weekday(weekday):
    wd=compact(weekday)
    if wd=='Monday': return '#12-30 evens'
    if wd=='Wednesday': return '#11-29 odds'
    return 'No Homework'
def reading_homework_for_weekday(weekday):
    wd=compact(weekday)
    if wd in {'Tuesday','Thursday'}: return 'Comprehension Questions'
    return 'No Homework'
def math_classwork_goal(): return '#1-10'
def reading_classwork_goal(): return 'Workbook'
def same_day_due_fields(entry_date):
    return {'dueDate':entry_date,'dueTime':'11:59 PM','timezone':'America/New_York','points':100,'gradeDisplay':'Percentage','unresolvedDueTime':False}
def assignment_due_payload(entry_date):
    return same_day_due_fields(entry_date)
MATH_CLASSWORK_DAYS=('Tuesday','Thursday')
READING_CLASSWORK_DAYS=('Monday','Wednesday')
MATH_HOMEWORK_GRADE_DAYS=('Monday','Wednesday')
READING_HOMEWORK_GRADE_DAYS=('Tuesday','Thursday')
GRADED_TITLE_SEP=' \u2014 '
def graded_selection_metadata(*,graded=True,selection_reason='',grade_category='instructional',grade_role='',selection_source='default',teacher_override_applied=False,default_selection=True,selected_day=''):
    return {'graded':graded,'selectionReason':selection_reason,'gradeCategory':grade_category,'gradeRole':grade_role,'selectionSource':selection_source,'teacherOverrideApplied':teacher_override_applied,'defaultSelection':default_selection,'selectedDay':selected_day}
def parse_graded_selection_overrides(week_meta=None,rows=None):
    overrides={'mathClassworkDay':None,'readingClassworkDay':None,'invalid':[]}
    payload=dict((week_meta or {}).get('gradedSelectionOverrides') or {})
    for r in rows or []:
        ro=jl(r.get('resolver_output') or '{}',{})
        sel=ro.get('gradedSelectionOverride') or ro.get('manualOverride') or {}
        classwork_day=sel.get('classworkDay')
        if compact(r.get('subject')).lower()=='math' and classwork_day:
            payload['mathClassworkDay']=compact(classwork_day)
        if compact(r.get('subject')).lower()=='reading' and classwork_day:
            payload['readingClassworkDay']=compact(classwork_day)
    math_day=compact(payload.get('mathClassworkDay') or '')
    if math_day:
        overrides['mathClassworkDay']=math_day if math_day in MATH_CLASSWORK_DAYS else None
        if math_day not in MATH_CLASSWORK_DAYS: overrides['invalid'].append({'field':'mathClassworkDay','value':math_day})
    reading_day=compact(payload.get('readingClassworkDay') or '')
    if reading_day:
        overrides['readingClassworkDay']=reading_day if reading_day in READING_CLASSWORK_DAYS else None
        if reading_day not in READING_CLASSWORK_DAYS: overrides['invalid'].append({'field':'readingClassworkDay','value':reading_day})
    return overrides
def row_for_subject_day(rows,subject,weekday):
    for r in rows:
        if compact(r.get('subject')).lower()==compact(subject).lower() and r.get('weekday')==weekday: return r
    return None
def math_lesson_row(rows,weekday):
    r=row_for_subject_day(rows,'math',weekday)
    if r and str(r.get('lesson','')).isdigit() and not str(r.get('tests','')).isdigit(): return r
    return None
def reading_lesson_row(rows,weekday):
    r=row_for_subject_day(rows,'reading',weekday)
    if r and str(r.get('lesson','')).isdigit() and not str(r.get('tests','')).isdigit(): return r
    return None
def math_written_assessment_on_day(rows,weekday='Tuesday'):
    r=row_for_subject_day(rows,'math',weekday)
    return bool(r and str(r.get('tests','')).isdigit())
def monday_reading_classwork_unavailable(rows,week_meta=None):
    r=row_for_subject_day(rows,'reading','Monday')
    return bool(r and str(r.get('tests','')).isdigit())
def resolve_math_classwork_day(rows,override=None):
    if override in MATH_CLASSWORK_DAYS: return override,'teacher-override',False
    if math_written_assessment_on_day(rows,'Tuesday'): return 'Thursday','assessment-displacement',True
    return 'Tuesday','default',True
def resolve_reading_classwork_day(rows,override=None,week_meta=None):
    if override in READING_CLASSWORK_DAYS: return override,'teacher-override',False
    if monday_reading_classwork_unavailable(rows,week_meta): return 'Wednesday','assessment-displacement',True
    return 'Monday','default',True
def build_week_graded_selection_context(rows,week_meta=None):
    overrides=parse_graded_selection_overrides(week_meta,rows)
    math_day,math_source,math_default=resolve_math_classwork_day(rows,overrides.get('mathClassworkDay'))
    reading_day,reading_source,reading_default=resolve_reading_classwork_day(rows,overrides.get('readingClassworkDay'),week_meta)
    return {'mathClassworkDay':math_day,'mathClassworkSelectionSource':math_source,'mathClassworkDefaultSelection':math_default and math_source=='default','readingClassworkDay':reading_day,'readingClassworkSelectionSource':reading_source,'readingClassworkDefaultSelection':reading_default and reading_source=='default','overrides':overrides,'assessmentWindowValidation':validate_assessment_schedule_windows(rows,week_meta,overrides)}
def math_homework_assignment_title(weekday,lesson_number):
    return f"SM5: {weekday} Homework{GRADED_TITLE_SEP}Lesson {lesson_number}"
def math_classwork_assignment_title(weekday,lesson_number):
    return f"SM5: {weekday} Classwork{GRADED_TITLE_SEP}Lesson {lesson_number}"
def reading_homework_assignment_title(weekday,lesson_number):
    return f"RM4: {weekday} Comprehension Questions{GRADED_TITLE_SEP}Lesson {lesson_number}"
def reading_classwork_assignment_title(weekday,lesson_number):
    return f"RM4: {weekday} Workbook Classwork{GRADED_TITLE_SEP}Lesson {lesson_number}"
def math_homework_assignment_description(weekday):
    if weekday=='Monday': return 'Classwork: #1-10\nHomework: #12-30 evens'
    if weekday=='Wednesday': return 'Classwork: #1-10\nHomework: #11-29 odds'
    return ''
def validate_assessment_schedule_windows(rows,week_meta=None,overrides=None):
    findings=[]; overrides=overrides or {}
    def add(code,severity,message,target,weekday=''):
        findings.append({'code':code,'severity':severity,'message':message,'target':target,'weekday':weekday})
    for r in rows or []:
        if not subject_active_for_quarter(r.get('subject'),week_meta): continue
        s=compact(r.get('subject')).lower(); wd=r.get('weekday') or ''; test=str(r.get('tests') or '').isdigit()
        if s=='math' and test:
            approved=bool((overrides or {}).get('mathWrittenAssessmentDay')==wd)
            if wd=='Tuesday' or approved: add('math-written.window','pass',f'Math Written Assessment on {wd} is within the approved Tuesday window',f'math-test-{r.get("tests")}',wd)
            else: add('math-written.window','warn',f'Math Written Assessment on {wd} is outside the default Tuesday window',f'math-test-{r.get("tests")}',wd)
            if wd in {'Tuesday','Wednesday','Thursday','Friday'}: add('math-fact.window','pass',f'Math Fact Assessment on {wd} is within the approved window',f'math-fact-{r.get("tests")}',wd)
            else: add('math-fact.window','warn',f'Math Fact Assessment on {wd} is outside the approved window',f'math-fact-{r.get("tests")}',wd)
        if s=='reading' and test:
            approved=bool((overrides or {}).get('readingMasteryTestDay')==wd)
            if wd=='Wednesday' or approved: add('reading-mastery.window','pass',f'Reading Mastery Test on {wd} is within the approved Wednesday window',f'reading-test-{r.get("tests")}',wd)
            else: add('reading-mastery.window','warn',f'Reading Mastery Test on {wd} is outside the default Wednesday window',f'reading-test-{r.get("tests")}',wd)
            if int(r.get('tests') or 0)<=13 and wd in {'Tuesday','Wednesday','Thursday','Friday'}: add('reading-fluency.window','pass',f'Reading Fluency Checkout on {wd} is within the approved window',f'reading-checkout-{r.get("tests")}',wd)
        if s=='spelling' and test:
            if wd in {'Tuesday','Wednesday','Thursday','Friday'}: add('spelling-test.window','pass',f'Spelling Test on {wd} is within the approved window',f'spelling-test-{r.get("tests")}',wd)
            else: add('spelling-test.window','warn',f'Spelling Test on {wd} is outside the approved window',f'spelling-test-{r.get("tests")}',wd)
        if s in {'history','science'} and test and wd=='Friday' and subject_active_for_quarter(s,week_meta): add(f'{s}-assessment.window','pass',f'{s.title()} assessment on Friday is within the approved window',f'{s}-test-{r.get("tests")}',wd)
        elif s in {'history','science'} and test and wd!='Friday' and subject_active_for_quarter(s,week_meta): add(f'{s}-assessment.window','warn',f'{s.title()} assessment on {wd} is outside the default Friday window',f'{s}-test-{r.get("tests")}',wd)
        if s in {'language-arts','shurley'} and test and wd=='Friday': add('shurley-assessment.window','pass',f'Language Arts assessment on Friday is within the approved window',f'ela-test-{r.get("tests") or r.get("lesson")}',wd)
        elif s in {'language-arts','shurley'} and test and wd!='Friday': add('shurley-assessment.window','warn',f'Language Arts assessment on {wd} is outside the default Friday window',f'ela-test-{r.get("tests") or r.get("lesson")}',wd)
    for bad in (overrides or {}).get('invalid') or []:
        add('graded-selection.override.invalid','warn',f"Invalid graded-selection override for {bad.get('field')}: {bad.get('value')}",bad.get('field') or 'override')
    return findings
def selected_graded_assignment_specs(rows,week_meta=None):
    if not rows: return []
    ctx=build_week_graded_selection_context(rows,week_meta); specs=[]; seen=set()
    def append_spec(kind,subject,title,text,row,*,grade_role,selection_reason,selection_source,default_selection,teacher_override_applied=False,grade_category='instructional',extra=None):
        key=(kind,subject,title,row.get('entry_date'))
        if key in seen: return
        seen.add(key)
        meta=graded_selection_metadata(graded=True,selection_reason=selection_reason,grade_category=grade_category,grade_role=grade_role,selection_source=selection_source,teacher_override_applied=teacher_override_applied,default_selection=default_selection,selected_day=row.get('weekday') or '')
        payload={'metadata':meta,'entry_date':row.get('entry_date'),'weekday':row.get('weekday') or ''}
        if extra: payload.update(extra)
        specs.append({'kind':kind,'subject':subject,'title':title,'text':text,'row':row,'payload':payload})
    mon=math_lesson_row(rows,'Monday')
    if mon:
        lesson=int(mon['lesson']); append_spec('assignment','math',math_homework_assignment_title('Monday',lesson),math_homework_assignment_description('Monday'),mon,grade_role='homework',selection_reason='owner-confirmed-monday-homework',selection_source='default',default_selection=True)
    wed=math_lesson_row(rows,'Wednesday')
    if wed:
        lesson=int(wed['lesson']); append_spec('assignment','math',math_homework_assignment_title('Wednesday',lesson),math_homework_assignment_description('Wednesday'),wed,grade_role='homework',selection_reason='owner-confirmed-wednesday-homework',selection_source='default',default_selection=True)
    math_cw_day=ctx['mathClassworkDay']; math_cw=math_lesson_row(rows,math_cw_day)
    if math_cw:
        lesson=int(math_cw['lesson']); append_spec('assignment','math',math_classwork_assignment_title(math_cw_day,lesson),'Classwork: #1-10',math_cw,grade_role='classwork',selection_reason=f'owner-confirmed-{math_cw_day.lower()}-classwork',selection_source=ctx['mathClassworkSelectionSource'],default_selection=ctx['mathClassworkDefaultSelection'],teacher_override_applied=ctx['mathClassworkSelectionSource']=='teacher-override')
    for wd in READING_HOMEWORK_GRADE_DAYS:
        row=reading_lesson_row(rows,wd)
        if row and reading_homework_for_weekday(wd)!='No Homework':
            lesson=int(row['lesson']); append_spec('assignment','reading',reading_homework_assignment_title(wd,lesson),'Homework: Comprehension Questions',row,grade_role='homework',selection_reason=f'owner-confirmed-{wd.lower()}-comprehension-homework',selection_source='default',default_selection=True)
    reading_cw_day=ctx['readingClassworkDay']; reading_cw=reading_lesson_row(rows,reading_cw_day)
    if reading_cw:
        lesson=int(reading_cw['lesson']); append_spec('assignment','reading',reading_classwork_assignment_title(reading_cw_day,lesson),'Classwork: Workbook',reading_cw,grade_role='classwork',selection_reason=f'owner-confirmed-{reading_cw_day.lower()}-workbook-classwork',selection_source=ctx['readingClassworkSelectionSource'],default_selection=ctx['readingClassworkDefaultSelection'],teacher_override_applied=ctx['readingClassworkSelectionSource']=='teacher-override')
    for r in rows:
        if not subject_active_for_quarter(r.get('subject'),week_meta): continue
        s=compact(r.get('subject')).lower(); test=int(r['tests']) if str(r.get('tests','')).isdigit() else None
        if s=='math' and test:
            append_spec('assignment','math',f'SM5: Written Assessment {test}','Local editable written assessment draft.',r,grade_role='assessment',selection_reason='scheduled-written-assessment',selection_source='pacing',default_selection=False,grade_category='assessment')
            fam=math_assessment_family(test,r['entry_date'],set()); append_spec('assignment','math',f'SM5: Fact Assessment {test}',fam['factTest']['practiceDescription'],r,grade_role='assessment',selection_reason='scheduled-fact-assessment',selection_source='pacing',default_selection=False,grade_category='assessment')
        elif s=='reading' and test:
            fam=reading_assessment_family(test,r['entry_date']); append_spec('assignment','reading',fam['readingTest']['title'],reading_test_description(test),r,grade_role='assessment',selection_reason='scheduled-mastery-test',selection_source='pacing',default_selection=False,grade_category='assessment',extra={'assessmentFamily':fam})
            if fam['checkout']: append_spec('assignment','reading',fam['checkout']['title'],checkout_description(test),r,grade_role='assessment',selection_reason='scheduled-fluency-checkout',selection_source='pacing',default_selection=False,grade_category='assessment')
        elif s=='spelling' and test:
            practice_start=max(1,test-4); append_spec('assignment','spelling',f'RM4: Spelling Test {test}',f'Practice Lessons {practice_start} through {test-1}.',r,grade_role='assessment',selection_reason='scheduled-spelling-test',selection_source='pacing',default_selection=False,grade_category='assessment')
        elif s in {'history','science'} and test:
            title=compact(r.get('title') or f"{s.title()} Assessment")
            if not title.startswith('HIST4:') and s=='history': title=f'HIST4: {title}'
            if not title.startswith('SCI4:') and s=='science': title=f'SCI4: {title}'
            append_spec('assignment',s,title,f'Local {s.title()} assessment draft.',r,grade_role='assessment',selection_reason=f'scheduled-{s}-assessment',selection_source='pacing',default_selection=False,grade_category='assessment')
        elif s in {'language-arts','shurley'} and test:
            title=compact(r.get('title') or 'ELA4: Assessment')
            if not title.startswith('ELA4:'): title=f'ELA4: {title}'
            append_spec('assignment','language-arts',title,'Local Language Arts assessment draft.',r,grade_role='assessment',selection_reason='scheduled-language-arts-assessment',selection_source='pacing',default_selection=False,grade_category='assessment')
    return specs
def instructional_grade_count(specs,subject):
    return sum(1 for s in specs if compact(s.get('subject')).lower()==subject and (s.get('payload') or {}).get('metadata',{}).get('gradeCategory')=='instructional')
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
    fact=resolve_fact_test(n); fid=stable_id('math-assessment-family',n,test_day)
    return {'assessmentFamilyId':fid,'testNumber':n,'writtenTestDate':test_day,'factTestDate':test_day,'announcementDraft':stable_id('math-test-announcement',fid),'factTest':fact}
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
CREATE TABLE IF NOT EXISTS homeroom_newsletter_months(id TEXT PRIMARY KEY,month_code TEXT NOT NULL,school_year TEXT NOT NULL,month_label TEXT NOT NULL,month_start TEXT NOT NULL,month_end TEXT NOT NULL,payload TEXT NOT NULL,version INTEGER NOT NULL DEFAULT 1,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,updated_by TEXT NOT NULL,UNIQUE(month_code,school_year));
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
            row=db.execute('SELECT * FROM weekly_plans WHERE starts_on=?',(iw['startsOn'],)).fetchone()
            return {
                'week': row_to_week(db,row) if row else None,
                'startup': sel,
                'startupPrompt': sel.get('startupPrompt') or ('Choose or create a week to begin.' if not row else None),
                'warning': sel.get('warning'),
                'instructionalWeek': iw,
                'weekChooser': True if not row else sel.get('mode')=='chooser',
            }
    def get_week(self,wid):
        with self.connect() as db: return row_to_week(db,db.execute('SELECT * FROM weekly_plans WHERE id=?',(wid,)).fetchone())
    def get_week_by_code(self,code):
        iw=instructional_week_by_code(code)
        if not iw: raise KeyError('week code not found')
        with self.connect() as db:
            row=db.execute('SELECT * FROM weekly_plans WHERE starts_on=?',(iw['startsOn'],)).fetchone()
            if not row: return None
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
        plan=db.execute('SELECT payload,starts_on FROM weekly_plans WHERE id=?',(wid,)).fetchone(); payload=jl(plan['payload'],{}); iw=payload.get('instructionalWeek') or instructional_week_by_starts_on(plan['starts_on']) or {}
        for r in rows:
            if not subject_active_for_quarter(r['subject'],iw):
                db.execute('UPDATE daily_subject_entries SET resolver_output=?,validation=?,in_class=?,at_home=? WHERE id=?',(jd({'assignmentPolicy':'untouched','reason':'inactive-quarter-subject','skipGeneration':True}),jd([]),'','',r['id']))
                continue
            resolver=resolver_for_daily(r,iw); val=[]
            if r['subject']=='reading' and resolver.get('assessmentFamily'):
                for wmsg in resolver['assessmentFamily'].get('warnings',[]): val.append({'severity':'warning','message':wmsg})
            agenda=agenda_fields_for_row(r,iw)
            db.execute('UPDATE daily_subject_entries SET in_class=?,at_home=?,resolver_output=?,validation=? WHERE id=?',(agenda.get('in_class',''),agenda.get('at_home',''),jd(resolver),jd(val),r['id']))
        replace_drafts(db,wid); replace_deployment(db,wid)
        if own: db.commit(); db.close()
        return self.get_week(wid) if own else {}
def resolver_for_daily(r,week_meta=None):
    lesson=int(r['lesson']) if str(r.get('lesson','')).isdigit() else None; test=int(r['tests']) if str(r.get('tests','')).isdigit() else None; s=r['subject']
    if s in {'history','science'} and week_meta and not subject_active_for_quarter(s,week_meta):
        return {'assignmentPolicy':'untouched','reason':'inactive-quarter-subject','agendaCapable':False,'skipGeneration':True}
    try:
        if s=='math' and test: return {'assessmentFamily':math_assessment_family(test,r['entry_date'],set())}
        if s=='math' and lesson: return resolve_math_lesson(lesson)
        if s=='reading' and test: return {'assessmentFamily':reading_assessment_family(test,r['entry_date'])}
        if s=='reading' and lesson: return resolve_reading_lesson(lesson)
        if s=='spelling' and test: return resolve_spelling_test(test)
        if s in {'history','science'}: return {'assignmentPolicy':'active','agendaCapable':True}
    except Exception as e: return {'error':str(e)}
    return {'status':'unresolved'}
def agenda_fields_for_row(r,week_meta):
    if not subject_active_for_quarter(r.get('subject'),week_meta): return {'in_class':'','at_home':''}
    s=r['subject']; wd=r['weekday']; lesson=int(r['lesson']) if str(r.get('lesson','')).isdigit() else None; test=int(r['tests']) if str(r.get('tests','')).isdigit() else None
    if s=='math' and lesson:
        return {'in_class':f"Lesson {lesson}\n{math_classwork_goal()}",'at_home':math_homework_for_weekday(wd)}
    if s=='math' and test:
        return {'in_class':f"Written Assessment {test}\nFact Assessment {test}",'at_home':'No Homework'}
    if s=='reading' and lesson:
        return {'in_class':f"Lesson {lesson}\n{reading_classwork_goal()}",'at_home':reading_homework_for_weekday(wd)}
    if s=='reading' and test:
        return {'in_class':f"Mastery Test {test}",'at_home':'No Homework'}
    if s=='spelling' and lesson:
        return {'in_class':f"Lesson {lesson}",'at_home':reading_homework_for_weekday(wd)}
    if s=='spelling' and test:
        return {'in_class':f"Spelling Test {test}",'at_home':'No Homework'}
    if compact(r.get('in_class')) or compact(r.get('at_home')): return {'in_class':compact(r.get('in_class','')),'at_home':compact(r.get('at_home','')) or 'No Homework'}
    if compact(r.get('title')): return {'in_class':compact(r.get('title','')),'at_home':'No Homework'}
    return {'in_class':'','at_home':''}
def collect_assessments_from_rows(rows,week_start,week_meta=None):
    out=[]; seen=set()
    for r in rows:
        if not subject_active_for_quarter(r.get('subject'),week_meta): continue
        test=int(r['tests']) if str(r.get('tests','')).isdigit() else None; s=r['subject']; ed=r['entry_date']
        if s=='reading' and test:
            fam=reading_assessment_family(test,ed); key=fam['assessmentFamilyId']
            if key in seen: continue
            seen.add(key)
            bullet=f"RM4: Mastery Test {test} on {weekday_for('',ed)} {ed}"
            if fam['checkout']: bullet=f"RM4: Mastery Test {test} and RM4: Fluency Checkout {test} on {weekday_for('',ed)} {ed}"
            out.append({'date':ed,'familyId':key,'bullet':bullet})
        if s=='math' and test:
            key=f'math-{test}-{ed}'
            if key in seen: continue
            seen.add(key); out.append({'date':ed,'familyId':key,'bullet':f"SM5: Written Assessment {test} and SM5: Fact Assessment {test} on {weekday_for('',ed)} {ed}"})
        if s=='spelling' and test:
            key=f'spell-{test}-{ed}'
            if key in seen: continue
            seen.add(key); out.append({'date':ed,'familyId':key,'bullet':f"RM4: Spelling Test {test} on {weekday_for('',ed)} {ed}"})
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
    if not items: items=['<li>&nbsp;</li>']
    return '<ul>'+''.join(items)+'</ul>'
def render_agenda_html(week_meta,rows,assessments=None,resources=None):
    iw=week_meta or {}; subtitle=iw.get('displaySubtitle') or f"Quarter {iw.get('quarter','?')}, Week {iw.get('week','?')}"
    week_start=iw.get('startsOn') or (rows[0]['entry_date'] if rows else ''); active_rows=[r for r in rows if subject_active_for_quarter(r.get('subject'),iw)]
    reminders=build_reminders_html(iw,assessments or collect_assessments_from_rows(active_rows,week_start,iw),[],week_start)
    parts=[f'<div id="kl_wrapper_3" class="kl_circle_left kl_wrapper" style="border-style: none;"><div id="kl_banner" class=""><p style="color: {WHITE}; background-color: {BLUE}; text-align: center; margin: 0;"><span style="font-size: 18pt;">&nbsp;Weekly Agenda</span><br><span style="font-size: 10pt;">{html.escape(subtitle)}</span></p><h3 style="background-color: {MAGENTA}; color: {WHITE}; border: 0 !important;">Reminders</h3><div style="width: 100%; padding-left: 15px;">{reminders}</div>']
    for idx,wd in enumerate(WEEKDAYS):
        dr=[r for r in active_rows if r['weekday']==wd]
        in_class_lines=[]
        homework_lines=[]
        for x in dr:
            fields=agenda_fields_for_row(x,iw)
            for line in compact(fields.get('in_class','')).split('\n'):
                if compact(line): in_class_lines.append(compact(line))
            hw=compact(fields.get('at_home','')) or 'No Homework'
            homework_lines.append(hw)
        in_class=''.join(f'<li>{html.escape(line)}</li>' for line in in_class_lines) or '<li>&nbsp;&nbsp;</li>'
        homework=''.join(f'<li>{html.escape(line)}</li>' for line in homework_lines) or '<li>No Homework</li>'
        parts.append(f'<div id="{DAY_BLOCK_IDS[idx]}" class=""><h3 style="color: {WHITE}; background-color: {BLUE}; margin-top: 15px; margin-bottom: 2px; border: 0 !important;">{wd}</h3><div style="display: flex; width: 100%;"><div style="width: 49%; padding-left: 15px;"><h4 class="kl_solid_border" style="color: {WHITE}; background-color: {DGRAY}; padding-left: 10px; margin: 0; border: 0 !important;">In Class</h4><ul>{in_class}</ul></div>')
        parts.append(f'<div style="width: 49%; padding-left: 15px;"><h4 class="kl_solid_border" style="color: {WHITE}; background-color: {DGRAY}; padding-left: 10px; margin: 0; border: 0 !important;">Homework</h4><ul>{homework}</ul></div>')
        parts.append('</div></div>')
    parts.append('</div></div>'); return ''.join(parts)
def assignment_drafts_for_day(r,week_meta=None,selection_ctx=None):
    return []
def assignment_drafts_for_week(rows,week_meta=None):
    specs=selected_graded_assignment_specs(rows,week_meta); out=[]
    for spec in specs:
        if spec.get('kind')!='assignment': continue
        due=assignment_due_payload(spec['row']['entry_date']); extra=dict(due); extra.update(spec.get('payload') or {})
        out.append((spec['kind'],spec['subject'],spec['title'],spec['text'],due,extra))
    return out
def replace_drafts(db,wid):
    db.execute('DELETE FROM drafts WHERE weekly_plan_id=?',(wid,)); rows=[dict(r) for r in db.execute('SELECT * FROM daily_subject_entries WHERE weekly_plan_id=? ORDER BY entry_date,subject',(wid,))]
    plan=db.execute('SELECT payload,starts_on FROM weekly_plans WHERE id=?',(wid,)).fetchone(); payload=jl(plan['payload'],{}); iw=payload.get('instructionalWeek') or instructional_week_by_starts_on(plan['starts_on']) or {}
    groups={'math':['math'],'reading-spelling':['reading','spelling'],'language-arts':['language-arts'],'history':['history'],'science':['science']}
    for key,subs in groups.items():
        if key in {'history','science'} and not any(subject_active_for_quarter(s,iw) for s in subs): continue
        rs=[r for r in rows if r['subject'] in subs and subject_active_for_quarter(r['subject'],iw)]
        if rs: insert_draft(db,wid,'page',key,f'{key} Agenda',f'{key} Agenda',render_agenda_html(iw,rs),{'subjects':subs,'instructionalWeek':iw})
    active_rows=[r for r in rows if subject_active_for_quarter(r.get('subject'),iw)]
    selection_ctx=build_week_graded_selection_context(active_rows,iw)
    for kind,sub,title,text,due,extra in assignment_drafts_for_week(active_rows,iw):
        insert_draft(db,wid,kind,sub,title,text,f'<p>{html.escape(text)}</p>',extra)
    for draft in build_week_announcement_drafts(active_rows,iw):
        insert_draft(db,wid,'announcement',draft['subject'],draft['title'],draft['body_text'],draft['body_html'],{'previewOnly':True,'teacherApprovalRequired':True,'announcementDraft':draft,'scheduleMetadata':draft.get('schedule_metadata',{}),'safetyMetadata':draft.get('safety_metadata',{})})
    starts_on=plan['starts_on'] or iw.get('startsOn') or ''
    if starts_on:
        _,newsletter,update=resolve_newsletter_for_week_start(starts_on,db=db,school_year='2026-2027',week_code=iw.get('code'))
        insert_draft(db,wid,'page',HOMEROOM_NEWSLETTER_SUBJECT,newsletter['title'],newsletter['body_text'],newsletter['body_html'],{'previewOnly':True,'teacherApprovalRequired':True,'artifactKind':'newsletter','cadence':'monthly','newsletterDraft':newsletter})
        insert_draft(db,wid,'announcement',HOMEROOM_NEWSLETTER_SUBJECT,update['title'],update['body_text'],update['body_html'],{'previewOnly':True,'teacherApprovalRequired':True,'artifactKind':'newsletter_update','announcementDraft':update,'safetyMetadata':update.get('safety_metadata',{}),'scheduleMetadata':None})
    insert_draft(db,wid,'daily_brief','homeroom','Daily Teacher Brief','Recipient: owen.reagan@thalesacademy.org\nSchedule: 6:15 AM America/New_York instructional days\nWeather: placeholder only.\nClassroom-safe joke: Why did the notebook smile? It had good margins.','<pre>Recipient: owen.reagan@thalesacademy.org</pre>',{'previewOnly':True})
def insert_draft(db,wid,kind,sub,title,text,html_body,payload): db.execute('INSERT INTO drafts(id,weekly_plan_id,kind,subject,title,body_text,body_html,status,idempotency_key,payload,created_at,updated_at,updated_by) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',(stable_id('draft',wid,kind,sub,title),wid,kind,sub,title,text,html_body,'draft',stable_id('idem',wid,kind,sub,title),jd(payload),now_utc(),now_utc(),'generator'))
def replace_deployment(db,wid):
    db.execute('DELETE FROM deployment_items WHERE deployment_plan_id IN (SELECT id FROM deployment_plans WHERE weekly_plan_id=?)',(wid,)); db.execute('DELETE FROM deployment_plans WHERE weekly_plan_id=?',(wid,)); pid=stable_id('deployment',wid)
    ops=['validate local weekly inputs','generate local assignment previews','render academic agenda previews','generate minimal assessment reminder previews','generate assessment announcement previews','generate monthly homeroom newsletter preview','await teacher approval']
    db.execute('INSERT INTO deployment_plans(id,weekly_plan_id,status,payload,created_at,updated_at,updated_by) VALUES(?,?,?,?,?,?,?)',(pid,wid,'preview_only',jd({'previewOnly':True,'canvasWritesAllowed':False,'emailSendsAllowed':False,'scheduleIntent':'Friday 4:00 PM America/New_York','operations':ops}),now_utc(),now_utc(),'generator'))
    for i,d in enumerate(db.execute('SELECT * FROM drafts WHERE weekly_plan_id=?',(wid,))):
        unresolved=['Teacher approval required']
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
    vals += [{'severity':'pass','message':'Phase 22 is preview-only: no Canvas writes and no email sends.'}]; return vals
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
    def db(self): db=WorkstationDB(self.db_path); db.migrate(); return db
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
                try:
                    wk=db.get_week_by_code(urllib.parse.unquote(path.rsplit('/',1)[-1]))
                    if wk is None: return self.sendj({'error':'week not found'},404)
                    return self.sendj(wk)
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
def command_init_db(a):
    db=WorkstationDB(a.db)
    db.migrate()
    print(f'Initialized empty Phase 22 database: {db.path}')
    return 0

def command_serve(a):
    db=WorkstationDB(a.db)
    db.migrate()
    Handler.db_path=db.path
    os.chdir(APP_DIR)
    srv=ThreadingHTTPServer((a.host,a.port),Handler)
    print(f'Phase 22 workstation serving at http://{a.host}:{a.port} db={db.path}')
    srv.serve_forever()
def command_self_test(a):
    import tempfile

    empty_path=Path(tempfile.mkdtemp())/'empty.sqlite3'
    empty_db=WorkstationDB(empty_path)
    empty_db.migrate()

    with empty_db.connect() as empty_conn:
        assert empty_conn.execute('SELECT COUNT(*) FROM pacing_entries').fetchone()[0] == 0
        assert empty_conn.execute('SELECT COUNT(*) FROM weekly_plans').fetchone()[0] == 0
        assert empty_conn.execute('SELECT COUNT(*) FROM daily_subject_entries').fetchone()[0] == 0
        assert empty_conn.execute('SELECT COUNT(*) FROM drafts').fetchone()[0] == 0

    empty_current=empty_db.current_week()
    assert empty_current['week'] is None
    assert empty_current['weekChooser'] is True

    with empty_db.connect() as empty_conn:
        assert empty_conn.execute('SELECT COUNT(*) FROM weekly_plans').fetchone()[0] == 0

    # Regression: get_week_by_code on empty DB must not create a week
    missing=empty_db.get_week_by_code('Q1W5')
    assert missing is None
    with empty_db.connect() as empty_conn:
        assert empty_conn.execute('SELECT COUNT(*) FROM weekly_plans').fetchone()[0] == 0
        assert empty_conn.execute('SELECT COUNT(*) FROM daily_subject_entries').fetchone()[0] == 0

    blank_week_id=empty_db.create_week('2026-08-17')
    blank_week=empty_db.get_week(blank_week_id)
    blank_math=next(item for item in blank_week['subjects'] if item['subject']=='math')
    assert len(blank_math['days']) == 5
    assert all(not day['lesson'] for day in blank_math['days'])

    with empty_db.connect() as empty_conn:
        assert empty_conn.execute('SELECT COUNT(*) FROM weekly_plans').fetchone()[0] == 1
        assert empty_conn.execute('SELECT COUNT(*) FROM pacing_entries').fetchone()[0] == 0

    # Explicitly created week is findable by code
    found_blank=empty_db.get_week_by_code('Q1W5')
    assert found_blank is not None
    assert found_blank['id'] == blank_week_id

    p=Path(tempfile.mkdtemp())/'w.sqlite3'
    db=WorkstationDB(p)
    db.migrate()
    db.seed_from_fixture()
    weeks=load_instructional_weeks(); assert len(weeks)==37; assert weeks[0]['code']=='Q1W1' and weeks[0]['startsOn']=='2026-07-20'; assert instructional_week_by_code('Q1W5')['startsOn']=='2026-08-17'
    assert canonical_week_code('Q1_W1')=='Q1W1'; assert canonical_week_code('q4-w10')=='Q4W10'
    assert resolve_reading_test(1)['lessonRange']=={'start':1,'end':10}; assert resolve_reading_test(10)['lessonRange']=={'start':91,'end':100}
    assert resolve_checkout(1)['fluency']=={'wpm':100,'maxErrors':2}; assert resolve_checkout(7)['fluency']=={'wpm':100,'maxErrors':2}
    assert resolve_checkout(8)['fluency']=={'wpm':115,'maxErrors':2}; assert resolve_checkout(10)['fluency']=={'wpm':115,'maxErrors':2}
    assert resolve_checkout(11)['fluency']=={'wpm':130,'maxErrors':2}; assert resolve_checkout(13)['fluency']=={'wpm':130,'maxErrors':2}
    assert resolve_checkout(2)['passage']=='The Field of Flowers'; assert resolve_checkout(13)['passage']=='The Prince with the Peasants'; assert resolve_checkout(2)['title']=='RM4: Fluency Checkout 2'
    fam=reading_assessment_family(2,'2026-07-21'); assert fam['assessmentFamilyId']; assert fam['sourceCheckoutKey']=='Check out 20'
    fam14=reading_assessment_family(14,'2026-07-21'); assert fam14['checkout'] is None and fam14['checkoutNumber'] is None and fam14['warnings']==[]; assert 'Checkout 14' not in reading_announcement_body(fam14); assert reading_checkout_number(14) is None
    assert resolve_math_lesson(1)['suggestedHomework']=='Odds'; assert resolve_fact_test(1)['powerUpCode']; assert resolve_reading_lesson(1)['page']==4
    w=db.current_week()['week']; d=w['subjects'][0]['days'][0]; up=db.patch_table('daily_subject_entries',d['id'],{'lesson':'1','title':'Lesson 1'},d['version'])
    assert up['version']==d['version']+1 and up['record']['title']=='Lesson 1'; assert db.patch_table('daily_subject_entries',d['id'],{'title':'stale'},d['version'])['status']==409
    by_code=db.get_week_by_code(w['payload'].get('instructionalWeek',{}).get('code') or canonical_week_code('Q1W1')); assert by_code and by_code['id']==w['id']; demo=build_payload(SYNTHETIC_FIXTURE_PATH,'synthetic-fixture'); assert demo['artifactClassification']=='synthetic-curriculum' and demo['containsStudentData'] is False
    up2=db.patch_table('daily_subject_entries',d['id'],{'title':'Lesson 2'},up['version']); assert up2['title']=='Lesson 2'
    db2=WorkstationDB(p); got=db2.get_week(w['id']); assert got['subjects'][0]['days'][0]['title']=='Lesson 2'
    db.generate_week(w['id']); html=''.join(x['body_html'] for x in db.get_week(w['id'])['drafts'])
    assert 'kl_wrapper_3' in html and 'Reminders</h3>' in html and 'Homework</h4>' in html and 'display: flex' in html and 'width: 49%' in html and 'In Class' in html
    assert 'Reminders &amp; Resources' not in html and '>At Home<' not in html and 'Study Guide' not in html
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
        prev=json.loads(urllib.request.urlopen(f'http://127.0.0.1:{port}/api/weeks/{w["id"]}/agenda-preview').read()); assert 'Reminders</h3>' in prev['html'] and 'Homework</h4>' in prev['html']
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
        # Phase 1: chooser with 37 weeks on empty DB
        wait_for_condition(cdp,"document.readyState === 'complete' && document.querySelectorAll('.week-chooser button[data-week-code]').length === 37")
        buttons=cdp.eval("Array.from(document.querySelectorAll('.week-chooser button[data-week-code]')).map((b) => b.dataset.weekCode)")
        assert len(buttons)==37 and len(set(buttons))==37
        for code in ['Q1W1','Q1W9','Q2W1','Q2W9','Q3W1','Q3W9','Q4W1','Q4W10']:
            assert code in buttons
        cdp.eval("window.__phase22FetchLog = []; window.__phase22OriginalFetch = window.fetch.bind(window); window.fetch = (...args) => { window.__phase22FetchLog.push(String(args[0])); return window.__phase22OriginalFetch(...args); };")
        cdp.eval("document.querySelector('[data-week-code=\"Q4W10\"]').click();")
        wait_for_condition(cdp,"document.getElementById('create-week-btn') !== null")
        wait_for_condition(cdp,"document.querySelector('#week-code').textContent === 'Q4W10'")
        fetch_log=cdp.eval("window.__phase22FetchLog || []")
        assert any('/api/weeks/by-code/Q4W10' in str(item) for item in fetch_log)
        assert cdp.eval(f"localStorage.getItem('{SELECTED_WEEK_STORAGE_KEY}')") == 'Q4W10'
        assert cdp.eval("document.querySelector('#week-grid').textContent.includes('No week loaded')")
        # Phase 2: explicit create + enter 5 Math values Mon-Fri
        cdp.eval("document.getElementById('create-week-btn').click();")
        wait_for_condition(cdp,"document.querySelector('#week-grid input[data-field=\"lesson\"]') !== null")
        cdp.eval("""
        (() => {
          var L = document.querySelectorAll('#week-grid input[data-field="lesson"]');
          var TS = document.querySelectorAll('#week-grid input[data-field="tests"]');
          L[0].value='18'; L[0].dispatchEvent(new Event('input',{bubbles:true}));
          L[1].value='19'; L[1].dispatchEvent(new Event('input',{bubbles:true}));
          L[2].value='20'; L[2].dispatchEvent(new Event('input',{bubbles:true}));
          TS[3].value='7'; TS[3].dispatchEvent(new Event('input',{bubbles:true}));
          L[4].value='21'; L[4].dispatchEvent(new Event('input',{bubbles:true}));
          return 'set';
        })()
        """)
        wait_for_condition(cdp,"document.querySelector('#save-state') && document.querySelector('#save-state').textContent === 'Saved'")
        # Phase 3: verify PATCH requests reached backend
        patch_paths=cdp.eval("(window.__phase22FetchLog||[]).filter(function(u){return u.indexOf('/api/daily-entries/')>=0})")
        assert len(patch_paths) >= 5
        patched_ids=set()
        for pp in patch_paths:
            for seg in pp.split('/'):
                if seg.startswith('p22-'):
                    patched_ids.add(seg)
        assert len(patched_ids) >= 5
        # Phase 4: verify SQLite contains exact values
        with sqlite3.connect(dbp) as conn:
            conn.row_factory=sqlite3.Row
            plan=conn.execute('SELECT * FROM weekly_plans').fetchone()
            assert plan is not None
            rows=conn.execute('SELECT * FROM daily_subject_entries WHERE weekly_plan_id=? AND subject=? ORDER BY entry_date',(plan['id'],'math')).fetchall()
            assert len(rows)==5
            assert rows[0]['lesson']=='18' and rows[0]['title']==''
            assert rows[1]['lesson']=='19'
            assert rows[2]['lesson']=='20'
            assert rows[3]['lesson']=='' and rows[3]['tests']=='7'
            assert rows[4]['lesson']=='21'
        # Phase 5: browser reload — all 5 values restored + header
        cdp.call('Page.reload',{'ignoreCache':True})
        wait_for_condition(cdp,"document.querySelectorAll('#week-grid input[data-field=\"lesson\"]').length===5&&document.querySelectorAll('#week-grid input[data-field=\"lesson\"]')[0].value==='18'&&document.querySelectorAll('#week-grid input[data-field=\"lesson\"]')[1].value==='19'&&document.querySelectorAll('#week-grid input[data-field=\"lesson\"]')[2].value==='20'&&document.querySelectorAll('#week-grid input[data-field=\"lesson\"]')[4].value==='21'&&(document.querySelectorAll('#week-grid input[data-field=\"tests\"]')[3]||{}).value==='7'&&document.querySelector('#week-code').textContent==='Q4W10'")
        assert cdp.eval(f"localStorage.getItem('{SELECTED_WEEK_STORAGE_KEY}')")=='Q4W10'
        # Phase 6: generate week after reload — wait for generated
        # drafts and deployment preview, not for inputs that were already
        # present before the asynchronous POST completed.
        # Inputs can render before main() finishes attaching the Generate
        # handler after reload. Wait for the handler itself before clicking.
        wait_for_condition(
            cdp,
            """
            (() => {
              const button=document.getElementById('generate-week');
              return button && typeof button.onclick === 'function';
            })()
            """,
        )

        # Record the Generate request immediately when it starts, then update
        # the same log entry when the response or error arrives.
        cdp.eval("""
        (() => {
          window.__phase22GenerateFetchLog=[];
          const originalFetch=window.fetch.bind(window);
          window.fetch=async (...args) => {
            const url=String(args[0]);
            const options=args[1] || {};
            const isGenerate=url.includes('/generate');
            const entry=isGenerate ? {
              url,
              method:String(options.method || 'GET').toUpperCase(),
              started:true,
              completed:false,
              status:null,
              ok:null,
              error:null,
            } : null;

            if (entry) window.__phase22GenerateFetchLog.push(entry);

            try {
              const response=await originalFetch(...args);
              if (entry) {
                entry.completed=true;
                entry.status=response.status;
                entry.ok=response.ok;
              }
              return response;
            } catch (error) {
              if (entry) {
                entry.completed=true;
                entry.error=String(error);
              }
              throw error;
            }
          };
        })()
        """)

        cdp.eval("document.getElementById('generate-week').click();")

        wait_for_condition(
            cdp,
            """
            (() => {
              const log=window.__phase22GenerateFetchLog||[];
              return log.length===1 && log[0].completed===true;
            })()
            """,
        )

        generate_fetch_log=cdp.eval(
            "window.__phase22GenerateFetchLog||[]"
        )
        assert len(generate_fetch_log)==1
        assert generate_fetch_log[0]['method']=='POST'
        assert generate_fetch_log[0]['error'] is None, generate_fetch_log
        assert generate_fetch_log[0]['status']==200, generate_fetch_log
        assert generate_fetch_log[0]['ok'] is True

        # Wait on the authoritative generated SQLite state first. Rendering
        # may lag behind the completed POST in slower headless runs.
        expected_draft_titles={
            'SM5: Written Assessment 7',
            'SM5: Fact Assessment 7',
        }
        deadline=time.monotonic()+30
        last_generation_state=None
        while time.monotonic()<deadline:
            with sqlite3.connect(dbp) as poll_conn:
                draft_titles={
                    row[0]
                    for row in poll_conn.execute(
                        """
                        SELECT title
                        FROM drafts
                        WHERE weekly_plan_id=? AND subject='math'
                        """,
                        (plan['id'],),
                    )
                }
                deployment_row=poll_conn.execute(
                    """
                    SELECT status, payload
                    FROM deployment_plans
                    WHERE weekly_plan_id=?
                    """,
                    (plan['id'],),
                ).fetchone()

            lesson_drafts_ok={
                math_homework_assignment_title('Monday',18),
                math_classwork_assignment_title('Tuesday',19),
                math_homework_assignment_title('Wednesday',20),
            }.issubset(draft_titles)
            assessment_drafts_ok=expected_draft_titles.issubset(draft_titles)
            deployment_ok=bool(
                deployment_row
                and deployment_row[0]=='preview_only'
                and jl(deployment_row[1],{}).get('canvasWritesAllowed') is False
            )

            last_generation_state={
                'draftTitles':sorted(draft_titles),
                'deploymentStatus':deployment_row[0] if deployment_row else None,
                'lessonDraftsOk':lesson_drafts_ok,
                'assessmentDraftsOk':assessment_drafts_ok,
                'deploymentOk':deployment_ok,
            }

            if lesson_drafts_ok and assessment_drafts_ok and deployment_ok:
                break
            time.sleep(0.1)
        else:
            raise AssertionError(
                f'generation did not reach expected SQLite state: '
                f'{last_generation_state}'
            )

        # After authoritative generation completes, prove the browser
        # rendered the generated drafts and blocked preview state.
        wait_for_condition(
            cdp,
            """
            (() => {
              const drafts=(document.querySelector('#draft-list')||{}).textContent||'';
              const deployment=(document.querySelector('#deployment-list')||{}).textContent||'';
              return drafts.includes('SM5: Monday Homework \u2014 Lesson 18')
                && drafts.includes('SM5: Wednesday Homework \u2014 Lesson 20')
                && drafts.includes('SM5: Tuesday Classwork \u2014 Lesson 19')
                && drafts.includes('SM5: Written Assessment 7')
                && drafts.includes('SM5: Fact Assessment 7')
                && !drafts.includes('Study Guide')
                && deployment.includes('blocked_preview');
            })()
            """,
        )

        # Generation must preserve the five teacher-entered values.
        assert cdp.eval(
            """
            (() => {
              const lessons=document.querySelectorAll(
                '#week-grid input[data-field="lesson"]'
              );
              const tests=document.querySelectorAll(
                '#week-grid input[data-field="tests"]'
              );
              return lessons.length===5
                && lessons[0].value==='18'
                && lessons[1].value==='19'
                && lessons[2].value==='20'
                && lessons[3].value===''
                && tests[3].value==='7'
                && lessons[4].value==='21';
            })()
            """
        ) is True

        deploy_text=cdp.eval(
            "(document.querySelector('#deployment-list')||{}).textContent||''"
        )
        assert 'blocked_preview' in deploy_text

        # Prove generation consumed the reloaded SQLite Math rows.
        with sqlite3.connect(dbp) as conn:
            conn.row_factory=sqlite3.Row
            generated_rows=conn.execute(
                """
                SELECT entry_date, lesson, tests, resolver_output
                FROM daily_subject_entries
                WHERE weekly_plan_id=? AND subject=?
                ORDER BY entry_date
                """,
                (plan['id'], 'math'),
            ).fetchall()
            assert len(generated_rows)==5

            generated_inputs=[
                (row['lesson'], row['tests'])
                for row in generated_rows
            ]
            assert generated_inputs==[
                ('18',''),
                ('19',''),
                ('20',''),
                ('','7'),
                ('21',''),
            ]

            generated_resolvers=[
                jl(row['resolver_output'],{})
                for row in generated_rows
            ]
            assert all(generated_resolvers)

            draft_titles={
                row['title']
                for row in conn.execute(
                    """
                    SELECT title
                    FROM drafts
                    WHERE weekly_plan_id=? AND subject='math'
                    """,
                    (plan['id'],),
                )
            }

            assert {
                math_homework_assignment_title('Monday',18),
                math_classwork_assignment_title('Tuesday',19),
                math_homework_assignment_title('Wednesday',20),
            }.issubset(draft_titles)
            assert 'SM5: Written Assessment 7' in draft_titles
            assert 'SM5: Fact Assessment 7' in draft_titles
            assert not any('Study Guide' in title for title in draft_titles)

            deployment=conn.execute(
                """
                SELECT status, payload
                FROM deployment_plans
                WHERE weekly_plan_id=?
                """,
                (plan['id'],),
            ).fetchone()
            assert deployment is not None
            assert deployment['status']=='preview_only'
            deployment_payload=jl(deployment['payload'],{})
            assert deployment_payload.get('previewOnly') is True
            assert deployment_payload.get('canvasWritesAllowed') is False

        # Phase 7: server restart — values survive
        server.terminate(); server.wait(timeout=5)
        server=subprocess.Popen(serve_cmd,cwd=APP_DIR,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        wait_for_http_json(f'http://127.0.0.1:{port}/api/health')
        cdp.call('Page.reload',{'ignoreCache':True})
        wait_for_condition(cdp,"document.querySelectorAll('#week-grid input[data-field=\"lesson\"]').length===5&&document.querySelectorAll('#week-grid input[data-field=\"lesson\"]')[0].value==='18'&&document.querySelectorAll('#week-grid input[data-field=\"lesson\"]')[1].value==='19'&&document.querySelectorAll('#week-grid input[data-field=\"lesson\"]')[2].value==='20'&&document.querySelectorAll('#week-grid input[data-field=\"lesson\"]')[4].value==='21'&&(document.querySelectorAll('#week-grid input[data-field=\"tests\"]')[3]||{}).value==='7'&&document.querySelector('#week-code').textContent==='Q4W10'")
        assert cdp.eval(f"localStorage.getItem('{SELECTED_WEEK_STORAGE_KEY}')")=='Q4W10'
        # Phase 8: non-404 error reaches "Load failed"
        cdp.call('Page.addScriptToEvaluateOnNewDocument',{'source':'''
          var _origFetch=window.fetch.bind(window);
          window.fetch=function(u,o){
            if(String(u).indexOf('/api/bootstrap')>=0) return new Response('{"error":"server error"}',{status:500,headers:{"Content-Type":"application/json"}});
            return _origFetch(u,o);
          };
        '''})
        cdp.call('Page.navigate',{'url':f'http://127.0.0.1:{port}/'})
        wait_for_condition(cdp,"document.querySelector('.workspace h2') && document.querySelector('.workspace h2').textContent === 'Load failed'")
        error_text=cdp.eval("document.querySelector('.workspace p').textContent") or ''
        assert 'week does not exist' not in error_text.lower()
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
