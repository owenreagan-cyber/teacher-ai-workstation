# Spotify Vibe Playlists

Spotify Vibe Playlists are a manual-only scaffold for the music layer of the Vibe Engine.

This phase does not add Spotify API code. It does not use OAuth. It does not store credentials, secrets, account tokens, or API keys.

## Playlist Ideas

The playlist concepts live in:

```text
configs/spotify-vibe-playlists.json
```

Concepts:

- Casual Anime.
- Teacher Coding.
- Planning Calm.
- Presentation Setup.
- Creative 3D Design.

Each concept includes search terms, a suggested manual playlist name, and notes.

## Manual Spotify Setup

For now:

1. Open Spotify manually.
2. Create the playlist by hand.
3. Use the suggested search terms as inspiration.
4. Keep classroom-facing playlists calm and appropriate.
5. Do not connect Spotify automation to Raycast, Shortcuts, or mode scripts yet.

## Future Automation Gate

Future Spotify automation must wait for a later approved capability phase.

That future phase must decide:

- which Spotify account is appropriate.
- where OAuth credentials live.
- how secrets are stored outside the repo.
- what account boundaries apply.
- how revocation and recovery work.

Do not store Spotify secrets in this repo.

Do not use a school account for paid/dev secrets if Owen's policy is to keep paid/dev subscriptions on a personal account.

## Safety

This scaffold does not:

- call Spotify APIs.
- use OAuth.
- create playlists automatically.
- store account credentials.
- touch Photos, wallpapers, Raycast, Apple Shortcuts, browser profiles, or iCloud.
