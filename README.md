python -m src.schema
python -m src.generate_data
python -m src.validate_data
python -m src.export_data
python -m pytest -v
python -m streamlit run src/dashboard.py