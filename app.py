import streamlit as st
import pandas as pd
import re
from io import BytesIO

@st.cache_data
def infer_email_structure(emails):
    patterns = []
    for email in emails.dropna():
        match = re.match(r'([a-zA-Z]+)\.?([a-zA-Z]+)?@(.+)', email)
        if match:
            first, last, domain = match.groups()
            patterns.append(('fl' if last else 'f', domain))
    if patterns:
        common_pattern, domain = max(set(patterns), key=patterns.count)
        return lambda f, l: f"{f.lower()}.{l.lower()}@{domain}" if common_pattern == 'fl' else lambda f, l: f"{f.lower()}@{domain}"
    return None

def fill_missing_emails(df):
    added_emails = []
    for company in df['Company Name'].unique():
        company_emails = df[df['Company Name'] == company]['Person Email']
        email_structure = infer_email_structure(company_emails)
        if email_structure:
            missing_rows = df[(df['Company Name'] == company) & (df['Person Email'].isnull())]
            for idx, row in missing_rows.iterrows():
                if pd.notnull(row['Person Forename']) and pd.notnull(row['Person Surname']):
                    inferred_email = email_structure(row['Person Forename'], row['Person Surname'])
                    df.at[idx, 'Person Email'] = inferred_email
                    added_emails.append(idx)
    return df, added_emails

st.title("Email Gap Filler")

uploaded_file = st.file_uploader("Upload CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("### Original Data", df.head())

    if st.button("Fill Missing Emails"):
        filled_df, added_emails = fill_missing_emails(df)
        st.success(f"Filled {len(added_emails)} emails.")
        
        def highlight_new_emails(val, idx):
            return 'background-color: lightgreen' if val.name in idx else ''

        st.write(filled_df.style.apply(lambda row: highlight_new_emails(row, added_emails), axis=1))

        buffer = BytesIO()
        filled_df.to_csv(buffer, index=False)
        st.download_button("Download Updated CSV", buffer.getvalue(), "updated_emails.csv")