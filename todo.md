# Code Review & Technical Debt Punch List

## 1. The `dashboard.py` Monolith
**Issue:** The Streamlit dashboard violates the Single Responsibility Principle. It handles database connection pooling, SQL execution, Pandas data manipulation, Altair chart rendering, and Streamlit UI layout all in one massive 300+ line class (`TransitDashboard`).
**Action Items:**
* [ ] **Extract Data Layer:** Create a `data_repository.py` or similar class to handle all SQLAlchemy connections and `pd.read_sql` calls.
* [ ] **Extract Visualization Layer:** Move the complex Altair chart builders (like the linear map and wait times) into a `charts.py` helper module.
* [ ] **Clean up Dead Code:** Remove the commented-out `st.set_page_config(...)` block at the top.
* [ ] **Clean up Dead Logic:** In `fetch_world_clock()`, remove the commented-out `#try:` and `# except:` blocks.

## 2. The "LLM-Style" / Conversational Comments
**Issue:** Several files contain overly verbose, conversational comments that read like a tutorial or a defense of a hack, rather than professional documentation.
**Action Items:**
* [ ] **`consumer.py` (Line 27):** Remove the diary-entry comment: *"However, I also want to bend the rules and make the dashboard "realtime" so this was my decision to not let the dashboard hang with "stale" data. I am aware I am mixing streaming..."* -> *Replace with a concise technical note about batch sizing for latency requirements.*
* [ ] **`consumer.py` (Line 41):** The `# NOTE: Data recovery strategy` block is good information, but too conversational. Condense it to standard docstring format explaining the idempotent UPSERT strategy.
* [ ] **`route.py` (Line 1):** Remove the conversational docstring: *"This is the closest thing to a brain that passengers and trains will have..."* -> *Replace with standard module-level documentation.*
* [ ] **`test_two_station_runtime.py`:** Many tests have verbose `Scenario:` descriptions (e.g., *"This demonstrates the logging of trains is accurate..."*). Trim these down to standard `Given / When / Then` testing docstrings.

## 3. Commented-Out & Dead Code
**Issue:** Leaving large blocks of commented-out code in the `main` branch creates confusion and clutter. Version control (Git) remembers old code; the files don't need to.
**Action Items:**
* [ ] **`test_four_station_spur_runtime.py`:** Delete the entire commented-out `test_zipper_merge_converging` function at the bottom of the file (since we replaced it with the diagnostic/fixed version earlier).
* [ ] **`consumer.py` (Line 39):** Remove `#clean_topic_functions["rail_segments"] = clean_rail_segments` if it is no longer being used.

## 4. Schema & Loader Cruft
**Issue:** Legacy data structures are lingering in the test configurations. 
**Action Items:**
* [ ] **`initial_loader_state.py`:** The `passenger_itinerary` and `passenger_routes` configs are somewhat redundant or overlapping in how they are mocked. Ensure the test loader strictly matches the columns required by the new dbt seed schema.
* [ ] **Test Assertions:** Double-check that all tests are evaluating the newly consolidated `total_passengers_in_system` correctly, rather than relying on old overlapping counts.