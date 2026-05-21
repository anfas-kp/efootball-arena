# Transfer System — Task Tracker

## Phase 1: Models & Database Schema
- [x] Add `is_transfer_listed`, `parent_club`, `is_on_loan`, `loan_expires` to `Player` model + `clean()`
- [x] Overhaul `TransferWindow` model (allowed_types, max_transfers, is_open property, clean)
- [x] Overhaul `TransferRequest` model (state machine, transfer_type, loan_end_date, VALID_TRANSITIONS, clean)
- [x] Create `PlayerRegistration` model
- [x] Enrich `TransferHistory` model (transfer_type, window, notes)
- [x] Update `admin.py` for new/changed models
- [x] Run `makemigrations` and `migrate`
- [x] Run `manage.py check` to verify

## Phase 2: Core Business Logic & Rules Engine
- [/] Create `exceptions.py`
- [/] Create `rules.py` with `TransferRules` class
- [/] Create `services.py` with `TransferService` class
- [/] Refactor views to use service layer

## Phase 3: REST API & Serializers
- [ ] Create `serializers.py`
- [ ] Add API views
- [ ] Add API URL routes

## Phase 4: Background Tasks
- [ ] Add `auto_manage_transfer_windows` task
- [ ] Add `expire_loans` task
- [ ] Add notification task

## Phase 5: UI & Templates
- [ ] Rebuild `transfer_hub.html`
- [ ] Create `admin_transfer_window.html`
- [ ] Update `admin_dashboard.html`
