# Reddit API Status

This file tracks the Reddit API request so the workstation roadmap does not forget it while other phases continue.

## Current status

```text
Status: pending Reddit review/approval
Submitted by: Owen Reagan
Purpose: personal local wallpaper/photo-widget inspiration workflow
Automation status: paused
```

## Submitted scope

Requested access was for a personal, local-only, read-only workflow that would inspect public subreddit listings and post metadata for a small number of anime/aesthetic wallpaper-related subreddits.

The request stated that the tool would not:

- post
- comment
- vote
- message users
- moderate communities
- profile users
- redistribute Reddit data
- sell data
- train AI models
- use Reddit content for commercial products

## Intended subreddits

```text
r/Animewallpaper
r/ImaginarySliceOfLife
r/Moescape
```

## Current decision

Do not build Reddit scanner/gatherer scripts until Reddit approval arrives.

Do not request Reddit passwords in local scripts.

Do not install weekly Reddit refresh automation.

## Resume criteria

Resume Reddit work only after one of these happens:

1. Reddit approves the request and provides a compliant API path.
2. Reddit denies the request and we document that Reddit automation is not available.
3. Owen chooses a different approved source for anime/aesthetic images.

## Next Reddit phase if approved

```text
0E-D3-B: Reddit auth setup
0E-D3-C: scanner and gatherer
0E-D3-D: optional weekly refresh after manual success
```
