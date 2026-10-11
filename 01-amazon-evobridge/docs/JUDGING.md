# EvoBridge Creator Assistant: judging notes

## Project description

Small creators often have an idea but lose momentum when editing tools ask them to make every production decision at once. EvoBridge turns a short bilingual conversation into a three-scene storyboard, keeps every change visible, and delivers a real video on the same computer.

The interaction is intentionally inspectable: the assistant asks for theme, audience, length and tone, then supports clear commands such as “Shorten scene 2”, “Text 2: …”, and “Undo”. A creator can move into direct scene editing, add a personal image, choose portrait or landscape, and explicitly confirm the exact revision to render. Progress, cancellation, persisted history and output evidence all refer to genuine jobs and files.

## Track and disclosure

Alexa+ main track, **web experience simulation**. This is an Alexa+ experience simulation built with AI-assisted development tools. The interaction layer uses bounded deterministic rules. It does not connect to the Alexa+ service. Storyboard edits and video rendering are implemented locally.

No Alexa logo is used. No runtime Alexa SDK, MCP interface, device, cloud LLM or AWS usage is claimed. Do not select optional AWS/Open Source mini-challenges without separately verifying and completing their requirements.

## What to judge in five minutes

1. Start the local server and choose a sample or create a brief conversationally.
2. Make two edits and undo one. Observe the stored revision and preview change.
3. Open export confirmation, cancel once, then confirm. Verify no job exists after cancellation and only one exists after a double click.
4. Watch the actual output and open its manifest. Compare two themes or aspect ratios.
5. Restart and observe restored projects, completed history and any explicitly interrupted jobs.

The free local reproduction path has no paid API or hosted uptime requirement. The source can remain runnable during the judging period. The owner still needs to provide the accepted repository access route and a public under-three-minute demo video.

## Development tools and rights

Implemented with OpenAI AI coding assistance, local shell tooling, Python, Pillow and FFmpeg. No runtime model. The generated code was exercised with standard-library unit tests and real-render evidence. The developer did not use an Alexa runtime toolchain and therefore does not claim hands-on Alexa SDK feedback. `FRICTION_LOG.md` reports only actual observations.

Upstream MIT code attribution, sample rights and third-party notices are preserved. All samples are synthetic text/geometry. See `PROVENANCE.md` for the shallow-baseline caveat and material changes.

## Submission gates, not completed claims

- Verify entrant/team eligibility and regional/service/prize requirements with the official organizer.
- Verify the necessary before-event baseline; the available public snapshot is dated September 23.
- Execute desktop/mobile browser smoke test and Windows startup on a real supported machine.
- Record the real UI with the supplied <3-minute script, including render progress and playback. English narration or complete English translation.
- Publish/share the repository with authorized judging access and upload the demo only after owner authorization. Recheck access through November 20.
- Complete Devpost fields and submit before **2026-10-23 19:00 UTC / 北京时间2026-10-24 03:00**.

Official rule references supplied for this build:
https://amazonappdev2026.devpost.com/rules
https://amazonappdev2026.devpost.com/forum_topics/45058-clarification-on-simulated-alexa-web-experience-requirements
https://amazonappdev2026.devpost.com/details/faqs
https://amazonappdev2026.devpost.com/forum_topics/45450-change-of-type-of-project-and-logo-permission

No publication, account creation, permissions change, purchase or competition submission was performed by this build task.
