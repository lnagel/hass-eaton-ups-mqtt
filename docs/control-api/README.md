# Control API research: protected application, shutdown sequencing, output control

Hand-off brief for implementing the control side of `eaton_ups_mqtt`
(researched 2026-10-04). Every fact is tagged:

- **[C]** confirmed — seen in an Eaton document, Eaton's Postman examples, this repo's
  own captures, or working third-party code.
- **[I]** inferred — strongly suggested but not seen end to end.
- **[?]** unknown — must be captured from a real card before coding (see §6).

Read §6 first if you are about to write code: three things are still unknown and the
capture scripts (`scripts/capture_rest_tree.py`, `scripts/dump_mqtt_data.py`) settle them on a real card in a few minutes.

---

## 1. Key insight: Home Assistant is already almost a protected application

- **[C]** Shutdown agents (Eaton IPP, IPM, third-party) talk to the card **only over its
  MQTT broker on 8883/tcp with mutual TLS**. There is no shared secret and no REST
  registration call. The client cert's CN is the MQTT clientId and the agent's identity.
  (M3 user guide §3.5.1, §4.2; M2 user guide §3.4; Eaton Gigabit card FAQ.)
- **[C]** Agent certs are trusted on the card under *Settings › Certificate › Trusted remote
  certificates › "Protected applications (MQTT)"*, or accepted automatically during the
  *Protection › Agents list › Start* pairing window. That is exactly the cert flow this
  integration already uses (`certificates.py`, Repairs download → upload to card).
- **[C]** An agent learns it must shut down by **subscribing**, not by being called:
  1. subscribe `mbdetnrs/<ver>/powerService/suppliers/+/identification`, pick the supplier whose
     `physicalName` is its load segment (`PRIMARY`, `GROUP 1`, `GROUP 2`);
  2. subscribe `mbdetnrs/<ver>/powerService/suppliers/{id}/schedule`;
  3. shut down when `delayBeforePowerDown >= 0` (and, if it has a shutdown duration,
     once `delayBeforePowerDown <= shutdownDuration`).
  Source: working agent [aximut/eaton-ups-mqtt-agent `index.js`](https://github.com/aximut/eaton-ups-mqtt-agent) (AGPL-3.0 — read, do not copy), tested on Network-M2.
- **[?]** How an agent reports its *name, version, Delay, OS shutdown duration* so it shows
  up in the card's Agents list and is counted in the shutdown sequence. The open-source
  agent publishes nothing; IPP must publish something. Candidates to check in a capture:
  `powerService/suppliers/{id}/shutdownDurations` (`{normal, critical}`),
  `powerService/suppliers/{id}/powerDownMinimumDurations` (`{normal, critical, emergency}`),
  `protectionService/clients`, a `powerService/consumers`-style tree. See §6.1.

The integration currently subscribes only to `managers/#`, `powerDistributions/#`,
`sensors/#` (`api.py::_subscribe_to_topics`). Adding `powerService/#`,
`protectionService/#`, `scheduleService/#` is the first step for every feature below.

## 2. Data model (what "supplier", "outlet", "group" mean)

| UI name (card) | `powerDistributions/1/outlets/{n}` | `powerService/suppliers/{id}` `physicalName` | Save/restore id |
|---|---|---|---|
| Entire UPS / Main output / Primary | `outlets/1` (`switchable: false` on 5PX) | `PRIMARY` | 1 |
| Outlets – Group 1 | `outlets/2` (`switchable: true`) | `GROUP 1` | 2 |
| Outlets – Group 2 | `outlets/3` (`switchable: true`) | `GROUP 2` | 3 |

- **[C]** Outlet ids, names and `switchable` from `tests/fixtures/mqtt_data_5px_2200_g2_m3.json`.
- **[C]** Supplier ids are opaque base64-ish strings (e.g. `acWPSUdxWmSxL4f849URrg`), see `docs/MQTT.md`. Match by `identification.physicalName`, never hard-code.
- **[C]** Network-M3 publishes/serves under **`mbdetnrs/2.0`**, M2 under `1.0` (fixture `@id`s; M3 Postman is "REST API version 2.0"). `const.py` already has both prefixes.
- **[C]** Supplier topics already documented in `docs/MQTT.md`: `identification`, `configuration`
  (`isControllable`, `isSwitchable`, `automaticSwitchOnEnabled`, `automaticSwitchOnDelay`,
  `powerCycleDuration`, `canProtect`…), `summary` (`protectingFor`, `poweringFor`,
  `protectionCapacityRuntime`, `protectionLowCapacityAlarm`…), `schedule`
  (`delayBeforePowerDown`, `delayBeforePowerUp`), `controllers` (links to
  `scheduleService/schedulers/{id}`, `protectionService/suppliers/{id}/triggers/power`, child
  suppliers), `shutdownDurations`, `powerDownMinimumDurations`, `estimatedPowerdownCommand`
  (`timepoint`, `severity`, `delay`).
- **[C]** REST GET `powerService/suppliers/{id}` advertises actions
  `#powerDown`, `#powerUp`, `#powerCycle` → `…/powerService/suppliers/{id}/actions/{action}`
  (`docs/eaton-network-m2-openapi.yaml`).
- **[C]** `protectionService` GET returns `clients`, `suppliers`, `configuration`; MQTT has
  `protectionService/suppliers`, `protectionService/actions` (`#scriptExec`).

## 3. Output / load-segment control

### 3.1 Two layers of commands

| Layer | Endpoint | Semantics |
|---|---|---|
| Raw outlet (immediate) | **[C]** `POST …/powerDistributions/1/outlets/{n}/actions/{switchOn,switchOff,cancelSwitchOn,cancelSwitchOff}` | Switches the outlet; `status.delayBeforeSwitchOff/On` (−1 = none) shows pending action. |
| Raw whole UPS | **[C]** `POST …/powerDistributions/1/actions/{switchOn,switchOff,switchOffWithAutoRestart,cancelSwitchOn,cancelSwitchOff}` | Whole-UPS output. |
| Protected ("Safe OFF / Safe reboot / Switch ON" in the UI) | **[C]** `POST …/powerService/suppliers/{id}/actions/{powerDown,powerUp,powerCycle}` exist | **[I]** Runs the agent shutdown sequence first, then cuts power (UI: "Protected applications will be safely powered down"). Body **[?]**. |

- **[C]** Raw actions are sent with **no body** in Eaton's Postman examples and in tuist's
  Go driver ([tuist#13655](https://github.com/tuist/tuist/pull/13655), `eaton.go` ~L133), which then
  polls `status.switchedOn`, treats a switch as pending while either delay `>= 0`, and refuses
  when `specifications.switchable == false`.
- **[I]** Optional delay argument: CLI example `rest exec /powerDistributions/1/outlets/1/actions/switchOn 5`
  (M3 guide §7.7.13) suggests a delay payload. JSON shape **[?]**.
- **[C]** Requires *Remote command = Enable* on the UPS (exposed as
  `powerDistributions/1/settings.remoteControlEnabled`); otherwise the card answers
  "This action is not allowed by the UPS". Surface this as a repair/issue.
- **[C]** UI access: Administrator and Operator only → REST account needs at least Operator.

### 3.2 Suggested HA entities

- `switch` per `switchable` outlet (Group 1/2): state from `outlets/{n}/status.switchedOn`;
  turn_off → protected `powerDown` on the matching supplier (safe), turn_on → `powerUp`.
- `button`s: "Safe reboot" (`powerCycle`), "Cancel pending" (`cancelSwitchOff/On`).
- `sensor`s: `delayBeforeSwitchOff/On`, supplier `schedule.delayBeforePowerDown/Up`
  (seconds, `None` when −1) — these are the countdowns users want on a dashboard.
- Optionally an "immediate off" service, clearly labelled as bypassing agents.

## 4. Shutdown sequencing configuration

### 4.1 Concepts (UI; M3 guide §3.5.2–3.5.3, M2 guide p.57–62)

- **[C]** Per load segment (Primary, Group 1, Group 2) a table of agents with **Delay (s)** and
  **OS shutdown duration (s)**. Shutdown time = max(Delay + OS duration) + 10 s; immediate
  shutdown time = max(OS duration) + 10 s. A **"local agent"** row sets a minimum shutdown
  duration / power-down delay for a segment with no agents (`localShutdownDuration`).
- **[C]** Power outage policy per segment: *Maximize availability* (default; finish 30 s before
  end of backup), *Immediate OFF* (start after 10 s on battery), *Load shedding* (M3),
  *Custom* (any of: on battery N s; capacity < X %; start/end N s before end of backup — first
  reached wins). If Primary goes off, groups go off too.
- **[C]** Low battery warning (UPS signals at ~2–3 min runtime) acts as a panic trigger.
- **[C]** Restart: optional forced reboot; wait for capacity > X %; restart Group 1 after N s,
  Group 2 after N s. Not editable on three-phase UPSs.

### 4.2 Field names (from the guides' Save/Restore JSON — nesting reconstructed **[I]**)

```text
powerOutagePolicy.settings.panicShutdownTriggers.onLowStateOfCharge   bool
powerOutagePolicy.settings.restart.enabled                            bool
powerOutagePolicy.suppliersSettings[].id                              1=Primary 2=Group1 3=Group2
powerOutagePolicy.suppliersSettings[].localShutdownDuration           s
shutdownTriggers.powerOutage.enabled                                  bool
shutdownTriggers.powerOutage.capacityLessThan                         %
shutdownTriggers.powerOutage.afterBackupTime                          s
shutdownTriggers.powerOutage.startShutdownBeforeEndOfBackup           s
shutdownTriggers.powerOutage.endShutdownBeforeEndOfBackup             s
```

The REST location of these (likely under `protectionService/configuration` or
`protectionService/suppliers/{id}/triggers/power`, which a supplier's `controllers` already links
to) is **[?]** → §6.2.

### 4.3 Related writable settings **[C]** (Network-M2 Postman)

```http
PUT /rest/mbdetnrs/1.0/powerDistributions/1
{"settings":{"audibleAlarmControl":"enabled","automaticRestartEnabled":true,
 "automaticRestartLevel":20,"forcedRebootEnabled":true,"remoteControlEnabled":true,
 "voltageHighDetection":144,"voltageLowDetection":60}}
```

`GET …/backupSystem/powerBank/settings` → `{"lowRuntimeThreshold":180,"lowStateOfChargeThreshold":23}` (PUT shape **[I]** same object).

### 4.4 Scheduled shutdown/restart **[C]** (M3 guide §3.4.4)

Columns: recurrence (0 once, 1 daily, 2 weekly), load segment (`scheduler` 1/2/3),
`shutdownTimeStamp`, `restartTimeStamp` (unix), active; global `schedule.enabled`. REST lives under
`scheduleService/schedules` / `scheduleService/schedulers/{id}` (GET confirmed; write body **[?]**).
Agent shutdowns run before the outlets power off. Operator role or above.

## 5. REST authentication notes **[C]**

- `POST /rest/mbdetnrs/<ver>/oauth2/token` with `{"username","password"}` (M2 examples also send
  `"grant_type":"password","scope":"GUIAccess"`). Response: `access_token`, `session`.
  Adding `"newPassword"` answers a forced password change.
- **One session per account**: a second login fails with error code `ConcurentSession` (sic).
  Log out with `DELETE /rest<session>` (the `session` value is a path). Recommend a dedicated card account for HA and
  always log out on unload (tuist `eaton.go` L39–470 documents this the hard way).
- Account changes need a re-auth bearer: `base64(access_token + ":" + password)`.
- The card uses a self-signed web cert — reuse the integration's existing pinning approach.
- MQTT is read-only from the agent's perspective as far as we know; **all commands go over REST**
  **[I]** (no command topic seen; `protectionService/actions` only shows `#scriptExec`).

## 6. Unknowns and how to settle them on a real card

### 6.1 Agent registration (what IPP publishes)
Run `scripts/dump_mqtt_data.py --duration 120` twice: once with no agent, once while an IPP
(free download) is paired and connected. Diff `powerService/*`, `protectionService/*`. Also check
the card's *Protection › Agents list* now: the HA integration's MQTT client may already appear
there as an agent.

### 6.2 Full REST tree for the control resources
`scripts/capture_rest_tree.py` walks `@id` links from `protectionService`,
`powerService`, `scheduleService`, `powerDistributions` (GET only, logs out at the end) and writes one
JSON file. Alternatively over SSH: `rest list -d 4 /protectionService` etc. (M3 guide §7.7.10–13).

### 6.3 Official write schemas
Eaton's NETWORK-M3 Postman collection (REST 2.0) is the only official source likely to contain
`powerService`/`protectionService` write bodies. It could not be fetched from the research sandbox
(truncated after `accountService`). `scripts/fetch_eaton_docs.sh` downloads it plus the
user guides on a normal machine; then convert it to OpenAPI. Note the raw API returns the Postman *collection* format (`item` tree), whereas `scripts/convert_postman_to_openapi.py` reads the documenter `data` export, so the converter needs a small adapter.

### 6.4 Action bodies
Once the above are in, verify `powerDown`/`powerUp`/`powerCycle` and outlet action bodies on
**Group 2 with nothing plugged in**, observing `schedule` and `outlets/3/status` over MQTT.

## 7. Sources

Eaton (official)
- NETWORK-M3 REST 2.0 Postman docs: <https://documenter.getpostman.com/view/7058770/2sAYdmmTha>
- Network-M2 REST 1.0 Postman docs (source of `docs/eaton-network-m2-postman.json`): <https://documenter.getpostman.com/view/7058770/2sAYBSjt7J>
- Rack PDU G4 Postman docs (same owner, similar model): <https://documenter.getpostman.com/view/7058770/2sAYHxo4T9>
- Network-M3 user guide (08/2024): protection p.52–67, controls/scheduling p.46–51, pairing p.180–181, CLI `rest` p.275–277 — <https://www.eaton.com/content/dam/eaton/products/backup-power-ups-surge-it-power-distribution/power-management-software-connectivity/eaton-gigabit-network-card/network-m3/resources/eaton-network-m3-user-guide.pdf>
- Network-M2 user guide (10/2024): protection p.52–62, controls p.49–50, pairing p.160–162 — <https://www.eaton.com/content/dam/eaton/products/backup-power-ups-surge-it-power-distribution/power-management-software-connectivity/eaton-gigabit-network-card/eaton-network-m2-user-guide.pdf>
- Gigabit Network Card FAQ (ports 8883 MQTT, 5353 mDNS): <https://www.eaton.com/us/en-us/catalog/backup-power-ups-surge-it-power-distribution/eaton-gigabit-network-card---na/gigabit-network-card-faq.html>
- Network-M2 release notes 3.0.5 / 2.0.5 / ≤1.7.5 (agent limits 30→20, MQTT changes, credential pairing in 1.4.3) — links in `fetch_eaton_docs.sh`
- IPP release notes (M2 shutdown delay option in 1.61, M3 support in 1.72): <https://www.eaton.com/content/dam/eaton/products/backup-power-ups-surge-it-power-distribution/power-management-software-connectivity/eaton-intelligent-power-protector/eaton-ipp-software-release-notes.txt>

Third-party code
- aximut/eaton-ups-mqtt-agent (AGPL-3.0) — MQTT-only shutdown agent: <https://github.com/aximut/eaton-ups-mqtt-agent>
- tuist/tuist PRs #13655, #13657 — Go driver for Eaton PDU/ATS cards (outlet switching, auth/session handling, `/rest/mbdetnrs/2.0`): <https://github.com/tuist/tuist/pull/13655>, <https://github.com/tuist/tuist/pull/13657> (path `infra/cluster-api-provider-tuist/internal/power/`)
- cfergs/eatonm2-powershell-module — config endpoints only: <https://github.com/cfergs/eatonm2-powershell-module>

Dead ends: NUT (SNMP only for these cards), Home Assistant forum, bitfocus companion request #1706.
