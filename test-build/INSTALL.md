# Klar NLU combined PR 289 + 290 test build

Version: **2026.10.3-rc.2892901**. Experimental build from staging base `26f701f3cfad1335fcda5c55a48250f7b52588e5`, with exactly PR 289 (`18a8a707`) and PR 290 (`abc3c2b4`) plus test packaging/version metadata. Both cherry-picks applied without conflicts. This is not upstream 2026.10.3 and does not include any other changes made after the shared base. Switching the upstream release channel to staging does not install these PRs.

The archive contains a prebuilt static Linux engine, built operator UI, local app Dockerfile/configuration, and the matching `custom_components/klar_nlu` integration. Choose the **amd64** archive for an x86-64 Proxmox VM. An aarch64 archive is provided for ARM64. Check HA Settings → System → Repairs → menu → System information (or `ha info`) for architecture. Do not install the wrong archive.

The test app has a separate slug `klar_nlu_pr289_pr290`, hostname `klar-nlu-pr289-pr290`, and private `/data` directory. It mounts HA configuration read-only. It has no published host ports by default and starts manually. Your current Klar app is retained for rollback. Installation builds the small container wrapper locally from the supplied binary/UI; it does not compile Rust or download an upstream Klar engine. Internet access is needed for the Debian runtime image and package updates.

## 1. Back up before making any changes

1. In HA Settings → System → Backups, create a manual backup including Home Assistant configuration and the existing Klar NLU app/data. Download it and the backup emergency kit to your computer; keep the encryption key. Prefer an additional Proxmox VM backup or snapshot with the VM shut down. Record the VM ID and snapshot name.
2. Record the current Klar app version (2026.10.3), app options, start-on-boot/watchdog state, integration engine mode, exact engine URL, release channel, exposure setting, and current HACS integration version. Store the app token and integration write token in a password manager, not in screenshots or shared logs. Confirm they match; reuse the same secret below.
3. Copy the entire currently installed HA configuration `custom_components/klar_nlu` directory to your computer, or outside `custom_components` into a backup directory. Do not leave a renamed integration directory inside `custom_components`. This is the exact integration rollback copy.
4. Open the existing Klar app UI → Settings → Settings backup. Download its settings archive. If LLM credentials are configured, enable inclusion of the API key and accept its confirmation so the test app receives the same credentials; store that archive securely. The archive covers `klar_nlu.json` (operator settings, calibration, rules, aliases, speech bank) and the stored LLM endpoint. It does not contain the app write token, HA integration entry, recordings, or all app-private history. The HA app backup remains the complete recovery copy. The original app's private data will not be copied or overwritten.
5. Temporarily disable HACS auto-updates for Klar NLU if enabled; avoid HACS update/redownload actions during the test. Record the prior setting.

## 2. Install the isolated test app

1. Extract this archive on your computer. Verify files against its `SHA256SUMS` if desired (`shasum -a 256 -c SHA256SUMS` from inside the extracted directory on macOS).
2. Using the Samba or SSH app, copy `local-apps/klar_nlu_pr289_pr290` into HA's **local app source directory**. Current HA calls it `/local_apps` (Samba share `local_apps`); older app/OS combinations expose `/addons` (Samba share `addons`). Use the actual local-source mount/share exposed by your system, not HA's `config` directory or `/addon_configs`. The result must be `LOCAL_SOURCE/klar_nlu_pr289_pr290/config.yaml`, with Dockerfile, engine, UI, and other files beside it. Do not nest the directory twice.
3. Open Settings → Apps → App store → menu → Check for updates, then refresh. Install **Klar NLU (PR 289 + 290 Test)** from Local apps. Leave the existing Klar NLU app installed. Leave the test app's network port mappings disabled; both apps can coexist on their internal container ports.
4. Set the test app's `token`, `support_bundle`, and `ui_locale` options to the values recorded from the existing app. Save and start the test app. Leave start-on-boot and watchdog off during initial testing.
5. Open its Web UI (Klar NLU Test). To authorize operator UI writes, use the token prompt/API token field when required; use the same secret. Restore the settings archive from step 1 in **this test app's** Settings backup page and confirm. Verify operator settings, calibration/rules, and LLM endpoint before proceeding. The stable app's `/data` remains untouched.

## 3. Install the matching integration and switch the existing entry

1. Copy the supplied `custom_components/klar_nlu` directory over the existing directory in HA configuration, replacing the complete directory after keeping the rollback copy. Keep the same `klar_nlu` domain; do not delete/recreate the integration entry or edit `.storage`.
2. Restart **Home Assistant Core** using its Restart command. A YAML reload alone does not replace Python integration code. HA OS/Supervisor does not need a reboot.
3. Go to Settings → Devices & services → the **existing** Klar NLU entry → Configure. Choose the **App/Docker (remote)** engine mode and set the exact URL to:

   `http://local-klar-nlu-pr289-pr290:10520`

   Supervisor DNS normalizes the local app's `local_klar_nlu_pr289_pr290` identity to this hostname; the configured alias `http://klar-nlu-pr289-pr290:10520` is an alternative. Use the identity hostname first. Keep the existing release channel and exposure setting; enter the same write token explicitly. Save. A custom URL is retained regardless of the stable/staging selector. Do not choose the bundled engine: this package's engine is supplied through the test app.
4. Leave the same Klar conversation agent/pipeline selected. After connection succeeds, stop the original Klar app and temporarily turn off its start-on-boot/watchdog (recorded earlier); keep it installed. Its data/options remain intact.

Only the integration's destination URL changes intentionally; the existing entry, entity IDs, Assist pipeline, exposure settings, and secret are retained. The matching integration includes Dutch window-list execution/speech support from PR 289, not merely the engine changes.

## 4. Verify before normal use

- Reload the existing Klar integration if necessary. It pushes the full registry at startup and retries while the engine is unavailable. Check HA logs for successful synchronization and the absence of HTTP 413/401 errors. Enabled entities are still sent in full; do not turn off exposure filtering or hide entities to reduce the upload. Existing graph/domain eligibility may make displayed graph counts differ from registry-upload counts.
- Check the test app's House view for known areas/devices and calibration. A 401 indicates a token mismatch; correct the test app option and integration write token, then restart the test app/reload integration. If DNS resolution fails, try the configured `klar-nlu-pr289-pr290` alias. Do not publish a host port as the first workaround.
- In the test app **Lab**, select Dutch (`nl`) and parse `Doe het licht in het kantoor uit` and `Kun je het licht in het kantoor even uitdoen?`: expect `HassTurnOff` for the office lights. Parse `Welke ramen staan er open?`: expect `HassGetState`, `binary_sensor`, `window`, `state=on`, `response=list`. Lab parsing does not send HA actions.
- Parse negative commands such as `Doe het licht in het kantoor niet uit` and `Kun je het licht in het kantoor niet uitdoen?`: they must not yield an executable turn-off plan. Start with Lab; spoken light commands through Assist really operate your lights.
- The home endpoint now accepts at most 8 MiB; 4,096 entities and the existing device/place/alias/field caps still apply. An installation exceeding those caps still receives a rejection. Your reported 2,216 entities fit the entity-count cap.
- Then test the read-only window question through the existing Dutch Assist pipeline. It should list open window sensors that are available under your existing exposure permissions. Test live light actions only when ready.

## 5. Roll back without losing the original app

1. If you want to retain changes made only in the test app, export its settings archive first; keep it separately. Do not restore test settings onto the stable app unless deliberately desired.
2. Start your original Klar NLU 2026.10.3 app with its existing options/data. In the existing integration's Configure form restore the exact original engine mode, URL, channel, exposure setting, and write token recorded in step 1. Save/reload and check connectivity.
3. Stop the test app and leave its start-on-boot/watchdog off. Restore the original app's previous start-on-boot/watchdog state.
4. Replace HA configuration `custom_components/klar_nlu` with your exact pre-test backup directory. Restart Home Assistant Core. Restore the prior HACS auto-update setting only after rollback verification. Keep the same integration entry and pipeline throughout.
5. Verify normal stable-engine behavior and the original settings. The original large-snapshot 413/Dutch issues may return, because rollback removes the fixes. Remove the local test app/source only after recovery is confirmed; uninstalling the test app deletes its private data, not the original app's data.
6. If an ordinary rollback fails, upload/restore the saved HA backup (including configuration and original Klar app) using HA's backup restore flow and its encryption key. A full restore replaces state and may discard changes since backup. A Proxmox VM restore is the separate last-resort recovery path.

No live HA/Proxmox instance was accessed during preparation. Automated tests and container smoke tests use synthetic fixtures, not your actual registries. This package has not been exercised inside your specific HA OS 2026.10.1 VM; the above final deployment checks are still required.

Official references: [local app installation](https://developers.home-assistant.io/docs/apps/tutorial/), [local app testing](https://developers.home-assistant.io/docs/apps/testing/), [HA OS backups and restore](https://www.home-assistant.io/common-tasks/os/#backups), [backup emergency kit](https://www.home-assistant.io/more-info/backup-emergency-kit).
