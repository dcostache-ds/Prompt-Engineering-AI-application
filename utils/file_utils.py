import io
import zipfile

def create_zip(dataframes):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for table_name, df in dataframes.items():
            csv_str = df.to_csv(index=False)
            csv_bytes = csv_str.encode('utf-8')
            zf.writestr(f"{table_name}.csv", csv_bytes)
    return buf.getvalue()
