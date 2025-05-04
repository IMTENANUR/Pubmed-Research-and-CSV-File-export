import streamlit as st
import pandas as pd
import requests
from xml.etree import ElementTree as ET

# Constants
BASE_URL_SEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
BASE_URL_FETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
MAX_RESULTS = 100

# PubMed Search Function
def query_pubmed(keywords):
    st.info(f"Searching PubMed for: **{keywords}**")
    search_params = {
        "db": "pubmed",
        "term": keywords,
        "retmode": "json",
        "retmax": MAX_RESULTS,
    }
    response = requests.get(BASE_URL_SEARCH, params=search_params)
    response.raise_for_status()
    result = response.json()
    return result.get("esearchresult", {}).get("idlist", [])

# Fetch Study Details
def fetch_study_details(pmids):
    results = []
    for pmid in pmids:
        fetch_params = {"db": "pubmed", "id": pmid, "retmode": "xml"}
        response = requests.get(BASE_URL_FETCH, params=fetch_params)
        response.raise_for_status()
        try:
            root = ET.fromstring(response.content)
            results.append({
                "PMID": pmid,
                "Title": root.findtext(".//ArticleTitle"),
                "Journal": root.findtext(".//Journal/Title"),
                "Publication Date": root.findtext(".//PubDate/Year"),
                "Authors": "; ".join(
                    author.findtext("LastName", "") + " " + author.findtext("ForeName", "")
                    for author in root.findall(".//Author")
                ),
                "DOI": root.findtext(".//ELocationID[@EIdType='doi']"),
                "Abstract": root.findtext(".//Abstract/AbstractText"),
                "Link": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            })
        except Exception as e:
            st.warning(f"Error parsing data for PMID {pmid}: {e}")
    return results

# Streamlit UI
st.set_page_config(page_title="PubMed Search Tool", layout="wide")
st.title("🔍 PubMed Keyword Search & Extractor")
st.markdown("Enter **any PubMed keywords** (e.g., `vitamin D AND pregnancy`) to search and extract structured study information.")

with st.form("pubmed_search_form"):
    keyword_input = st.text_input("🔎 Enter PubMed Search Keywords", "ketoconazole AND dandruff")
    submitted = st.form_submit_button("Search")

if submitted:
    with st.spinner("Fetching data..."):
        try:
            pmids = query_pubmed(keyword_input)
            if not pmids:
                st.warning("No results found.")
            else:
                data = fetch_study_details(pmids)
                df = pd.DataFrame(data)
                st.success(f"{len(df)} studies found.")
                st.dataframe(df)

                # Download CSV
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name="pubmed_results.csv",
                    mime="text/csv"
                )
        except Exception as e:
            st.error(f"An error occurred: {e}")
