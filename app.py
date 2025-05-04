
import streamlit as st
import pandas as pd
import requests
from xml.etree import ElementTree as ET
from io import BytesIO

# PubMed API URLs
BASE_URL_SEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
BASE_URL_FETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
MAX_RESULTS = 100


# PubMed query function
def query_pubmed(ingredient, focus):
    st.info(f"Querying PubMed for **{ingredient}** ({focus})...")
    search_params = {
        "db": "pubmed",
        "term": f"{ingredient} AND {focus}",
        "retmode": "json",
        "retmax": MAX_RESULTS,
    }
    response = requests.get(BASE_URL_SEARCH, params=search_params)
    response.raise_for_status()
    search_data = response.json()
    pmids = search_data.get("esearchresult", {}).get("idlist", [])
    return pmids


# Fetch study details
def fetch_study_details(pmids, ingredient):
    studies = []
    for pmid in pmids:
        fetch_params = {"db": "pubmed", "id": pmid, "retmode": "xml"}
        fetch_response = requests.get(BASE_URL_FETCH, params=fetch_params)
        fetch_response.raise_for_status()

        try:
            root = ET.fromstring(fetch_response.content)
            study = {
                "Ingredient": ingredient,
                "PMID": pmid,
                "Title": root.findtext(".//ArticleTitle"),
                "Journal": root.findtext(".//Journal/Title"),
                "PublicationDate": root.findtext(".//PubDate/Year"),
                "Authors": "; ".join(
                    author.findtext("LastName", "") + " " + author.findtext("ForeName", "")
                    for author in root.findall(".//Author")
                ),
                "DOI": root.findtext(".//ELocationID[@EIdType='doi']"),
                "Abstract": root.findtext(".//Abstract/AbstractText"),
                "PubMed Link": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            }
            studies.append(study)
        except Exception as e:
            st.error(f"Error parsing PMID {pmid}: {e}")
    return studies


# Streamlit UI
st.title("🧪 PubMed Ingredient Clinical Trials Explorer")

with st.form("pubmed_query"):
    ingredient_input = st.text_input("Enter Ingredient Name", "Ketoconazole")
    focus_input = st.text_input("Enter Focus Terms", "dandruff AND anti-hairloss")
    submit_btn = st.form_submit_button("Search")

if submit_btn:
    with st.spinner("Fetching studies from PubMed..."):
        try:
            pmids = query_pubmed(ingredient_input, focus_input)
            if not pmids:
                st.warning("No studies found.")
            else:
                results = fetch_study_details(pmids, ingredient_input)
                df = pd.DataFrame(results)
                st.success(f"Found {len(df)} studies.")
                st.dataframe(df)

                # CSV download
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"{ingredient_input.replace(' ', '_')}_studies.csv",
                    mime="text/csv",
                )
        except Exception as e:
            st.error(f"Error occurred: {e}")
