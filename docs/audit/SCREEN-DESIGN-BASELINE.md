# MADO-queue Screen Design Baseline

## 1. Purpose

This document records a fork-side audit baseline for MADO-queue screen design.

It organizes the role, users, displayed information, operations, state transitions, and review points for each screen.

This is not an upstream specification. It is an external audit note intended to support issue triage, UI change review, UX observation, and future documentation proposals.

## 2. Target Screens

| URL | Screen | Main users | Purpose |
|---|---|---|---|
| `/` | Ticket issuing screen | Visitor / guide staff | Select procedure type and issue a ticket |
| `/processing` | Processing management screen | Counter staff | View waiting tickets, call numbers, start and complete processing |
| `/display` | Public display screen | Waiting-room visitors | View currently called numbers and waiting status |

## 3. Basic Screen Design Principles

### 3.1 Visitor-facing screens should avoid hesitation

Visitors are not system users in the usual sense. They are people arriving at a municipal counter, often with a concrete concern or procedure.

The ticket issuing screen should prioritize:

- clear choices
- readable wording
- large tap targets
- clear next action after issuing a ticket
- minimal need for explanation

### 3.2 Staff-facing screens should preserve operational state

Counter staff need to understand the current operational state quickly.

The processing screen should make it hard to confuse:

- waiting
- called
- processing
- absent / returned to waiting
- completed
- deleted / canceled

### 3.3 Public display should prioritize distance readability

The display screen is used in a waiting-room context.

It should prioritize:

- large text
- high visibility
- limited information density
- clear called number display
- recognition by both visual and audio cues

### 3.4 Screen changes should be reviewed as workflow changes

A screen change may look small in code, but it can change visitor behavior or staff operation.

When labels, colors, layout, buttons, update intervals, or displayed states change, the review should record who is affected and what operational behavior may change.

## 4. Ticket Issuing Screen `/`

### 4.1 Users

- Visitors
- Guide staff
- Tablet users

### 4.2 Purpose

The screen allows a visitor or guide staff member to select a procedure category and issue a numbered ticket.

### 4.3 Main Actions

- Select procedure type
- Issue a ticket
- Receive printed ticket if the selected category prints
- Record non-printing visitor count for category D

### 4.4 Displayed Information

The screen should display only the information needed for issuing a ticket.

Typical information includes:

- procedure buttons
- category or procedure labels
- issue feedback after tapping
- printing or completion feedback

### 4.5 Design Risks

Potential risks:

- procedure labels are written in staff-internal terminology
- visitors cannot decide which button to press
- print and non-print categories are confused
- buttons are too small for tablet use
- double-tap or repeated ticket issuing occurs while printing
- the visitor does not understand what to do after receiving the ticket

### 4.6 Review Questions

When reviewing a change to `/`, ask:

- Can a first-time visitor understand the choices?
- Are the button labels written from the visitor's point of view?
- Does the screen make the next action clear?
- Is there a risk of duplicate issuing?
- Does the change affect printed ticket content?
- Does the change affect logs or counters?
- Does category D remain understandable as a non-printing count?

## 5. Processing Management Screen `/processing`

### 5.1 Users

- Counter staff
- Staff responsible for queue management
- Staff checking congestion or current processing state

### 5.2 Purpose

The screen allows staff to manage the lifecycle of issued tickets.

It supports viewing waiting tickets, calling a ticket, handling absence, completing processing, and deleting or canceling unnecessary tickets.

### 5.3 Main Actions

- View waiting list
- Call a number
- Mark as processing
- Return absent visitor to waiting state
- Complete processing
- Delete / cancel unnecessary ticket
- Observe current congestion

### 5.4 Displayed Information

The screen should make current operational state clear.

Typical information includes:

- waiting tickets
- category
- ticket number
- procedure label
- elapsed waiting time
- called / processing state
- completed or deleted state where applicable
- staff count where used

### 5.5 Design Risks

Potential risks:

- waiting, processing, completed, and deleted states are visually confused
- delete operation is mistaken for completion
- deleted history is misunderstood as physically removed data
- staff assume the screen is real-time when it is updated at intervals
- multiple staff operate the same ticket at the same time
- the screen does not make congestion visible enough for operational decisions

### 5.6 Review Questions

When reviewing a change to `/processing`, ask:

- Are ticket states distinguishable?
- Are irreversible or sensitive operations clearly separated?
- Does the UI match the actual DB state transition?
- Does the change affect `event_logs` or `processing_logs`?
- Can staff understand the meaning of deletion / cancellation?
- Is the update interval and possible display lag acceptable?
- Would a non-technical staff member understand the operation?

## 6. Public Display Screen `/display`

### 6.1 Users

- Waiting-room visitors
- Guide staff
- Counter staff

### 6.2 Purpose

The screen displays currently called numbers and waiting status in the waiting room.

It supplements voice calls and helps visitors recognize when they are called.

### 6.3 Main Display Elements

- Current called number
- Waiting count
- Category or procedure information where needed
- Visual call update
- Audio chime where supported

### 6.4 Design Risks

Potential risks:

- text is too small for a 32-inch or larger waiting-room display
- too much information reduces readability
- visitors cannot tell when the called number changes
- audio-only notification is insufficient
- visual-only notification is insufficient
- category notation confuses visitors
- waiting count is misunderstood

### 6.5 Review Questions

When reviewing a change to `/display`, ask:

- Can the called number be read from a distance?
- Is the most important information visually dominant?
- Does the screen avoid unnecessary detail?
- Does the visitor notice a new call?
- Does it work when audio is missed?
- Does it work when visual attention is elsewhere?
- Does the waiting count communicate the intended meaning?

## 7. Cross-Screen State Model

The screens are connected by ticket state transitions.

A simplified model is:

```text
issued
-> waiting
-> called / processing
-> completed
```

Alternative or exceptional paths include:

```text
issued
-> waiting
-> absent / returned to waiting
```

```text
issued
-> waiting
-> deleted / canceled
```

Screen design should not obscure these state transitions.

If the implementation uses logs to infer current state, the UI should still present a clear operational state to staff.

## 8. Screen Change Review Checklist

A screen-related pull request or issue should explain:

- target screen
- target user
- current behavior
- proposed behavior
- reason for change
- operational benefit
- risk of misoperation
- impact on DB and logs
- impact on printed ticket if any
- screenshots or screen recordings if available
- whether staff operation changes
- whether visitor behavior changes
- whether documentation must be updated

## 9. Relationship to UX Observations

This document should be used together with `UX-OBSERVATION-MODEL.md`.

- Screen design baseline records what each screen is for.
- UX observation records what actually happens in use, operation, review, or maintenance.

A UX observation should not immediately become a UI change.

It should first be classified as one of:

- wording change
- layout change
- state-transition clarification
- workflow documentation
- operational procedure update
- requirement clarification
- governance or contribution-process issue

## 10. Relationship to v1.0.0 Baseline

This screen design baseline should be read together with `V1.0.0-BASELINE-DOCUMENTATION.md`.

At `v1.0.0`, the documented screen set is:

- `/` for ticket issuing
- `/processing` for staff processing management
- `/display` for public waiting-room display

Any future change that changes these screens' roles, users, or operational meaning should be reviewed as a baseline-impacting change, even if the code change appears small.

## 11. Current Assessment

The current screen structure is simple and suitable for a small-start municipal counter system.

The main audit concern is not visual polish. The main concern is whether each screen continues to support the intended municipal workflow without increasing confusion, staff burden, operational ambiguity, or maintenance risk.
