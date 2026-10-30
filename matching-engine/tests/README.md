To run the tests, you must first activate the virtual environment and then run pytest:

(.venv) &gt; .venv/Scripts/activate  
(.venv) &gt; pytest -q





Add unit tests for price-time priority, partial fills, invalid quantities, market-order remainder handling, and symbol isolation. The demo engine currently uses insertion order and is not production-grade.
