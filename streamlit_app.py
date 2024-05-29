#######################
# Import libraries
import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
import subprocess
import sys
import typing

import httpx
import pandas
from lxml import html, etree
import os
import pickle

from streamlit_tree_select import tree_select




#######################
# Page configuration
st.set_page_config(
    page_title="US Population Dashboard",
    page_icon="🏂",
    layout="wide",
    initial_sidebar_state="expanded")

alt.themes.enable("dark")


#######################
# Load data (old stuff)
df_reshaped = pd.read_csv('data/us-population-2010-2019-reshaped.csv')
#
selected_color_theme = "blues"
selected_year = 2018

### define what information about the repositories should be requested
def safe_get_first(xpath_result):
    """Safely get the first item from the XPath result or return None if empty."""
    return xpath_result[0] if xpath_result else None


def extract_repository_info(
    repository_metadata_xml: html.HtmlElement,
) -> typing.Dict[str, typing.Any]:
    """Extracts wanted metadata elements from a given repository metadata xml representation.

    Args:
        repository_metadata_xml: XML representation of repository metadata.

    Returns:
        Dictionary representation of repository metadata.

    """

    namespaces = {"r3d": "http://www.re3data.org/schema/2-2"}
    return {
        "re3data_id": repository_metadata_xml.xpath("//re3data.orgidentifier/text()", namespaces=namespaces)[0],  ## put the '[0]' if I know there is to be exactly one element
        "name": repository_metadata_xml.xpath("//repositoryname/text()", namespaces=namespaces)[0],
        "type": repository_metadata_xml.xpath("//type/text()", namespaces=namespaces),
        "identifier": repository_metadata_xml.xpath("//repositoryidentifier/text()", namespaces=namespaces),
        "url": safe_get_first(repository_metadata_xml.xpath("//repositoryurl/text()", namespaces=namespaces)), ## use this function if ur not sure if there is an element
        "subjects": repository_metadata_xml.xpath("//subject/text()", namespaces=namespaces),
        "keywords": repository_metadata_xml.xpath("//keyword/text()", namespaces=namespaces),
        "metadataStandards": repository_metadata_xml.xpath("//metadatastandardname/text()", namespaces=namespaces)
    }


@st.cache_data
def load_or_query_re3data(file_path):
    """
    Load repository metadata from a file or query the re3data API if the file does not exist.

    This function checks if a dump file with serialized XML content exists at 'file_path'.
    If the file exists, it loads the XML data from the file. If the file does not exist, it fetches
    the metadata from the re3data API, serializes the XML data, and saves it to the file at 'file_path'.

    Parameters:
    file_path (str): The path to the file where the serialized XML content is stored or will be saved.

    Returns:
    list of str: A list of serialized XML strings representing the repository metadata.

    Usage:
    file_path = "./data/re3data_repo_dump"
    data = load_or_query_re3data(file_path)
    """
    
    results = []

    # Check if the dump file already exists
    if os.path.exists(file_path):
        # Load the list of XML content from the file
        with open(file_path, 'rb') as f:
            xml_strings = pickle.load(f)
        results = xml_strings  # Already serialized XML strings
        print("Loaded data from the dump file.")
    else:
        # If the file does not exist, run the harvesting code

        # Obtain URLs for further API queries
        URL = "https://www.re3data.org/api/beta/repositories"
        re3data_response = httpx.get(URL, timeout=60)
        urls = html.fromstring(re3data_response.content).xpath("//@href")

        with httpx.Client() as client:
            for url in urls:
                repository_metadata_response = client.get(url)
                repository_metadata_xml = html.fromstring(repository_metadata_response.content)
                results.append(etree.tostring(repository_metadata_xml).decode('utf-8'))

        # Save the serialized XML strings to a file
        with open(file_path, 'wb') as f:
            pickle.dump(results, f)
        print(f"Harvested data and saved to {file_path}.")

    return results

# Usage example:
re3data_xml_dump = load_or_query_re3data("./data/re3data_repo_dump")

######### Parse the dump

@st.cache_data
def parse_query_results_into_df(query_results):
    """
    Parse the query results into a pandas DataFrame.

    This function takes a list of serialized XML strings, converts them back into
    XML elements, and then extracts the repository information to construct a DataFrame.

    Parameters:
    query_results (list of str): A list of serialized XML strings representing the repository metadata.

    Returns:
    pandas.DataFrame: A DataFrame containing the parsed repository information.
    """
    parsed_entries = []

    for xml_str in query_results:
        xml_element = html.fromstring(xml_str)
        parsed_entries.append(extract_repository_info(xml_element))

    return pd.DataFrame(parsed_entries)

pd_parsed = parse_query_results_into_df(re3data_xml_dump)


pd_exploded = pd_parsed.explode("subjects")
pd_grouped = pd_exploded.groupby(by="subjects").size().reset_index(name='counts')



#######################
### re3data stuff






#######################

# Sidebar
with st.sidebar:
    #st.title('🏂 US Population Dashboard')
    st.title("🐙 Streamlit-tree-select")
    st.subheader("A simple and elegant checkbox tree for Streamlit.")

    st.metric(label="# of selected repos:", value=pd_parsed.shape[0], delta=(pd_parsed.shape[0]-3216))

    # Create nodes to display
    nodes = [{'label': '1 Social and Behavioural Sciences',
  'value': '1 Social and Behavioural Sciences',
  'children': [{'label': '1-01 Ancient Cultures',
    'value': '1-01 Ancient Cultures',
    'children': [{'label': '1-01-01 Prehistory',
      'value': '1-01-01 Prehistory'},
     {'label': '1-01-02 Classical Philology',
      'value': '1-01-02 Classical Philology'},
     {'label': '1-01-03 Ancient History', 'value': '1-01-03 Ancient History'},
     {'label': '1-01-04 Classical Archaeology',
      'value': '1-01-04 Classical Archaeology'},
     {'label': '1-01-05 Egyptology and Ancient Near Eastern Studies',
      'value': '1-01-05 Egyptology and Ancient Near Eastern Studies'}]},
   {'label': '1-02 History',
    'value': '1-02 History',
    'children': [{'label': '1-02-01 Medieval History',
      'value': '1-02-01 Medieval History'},
     {'label': '1-02-02 Early Modern History',
      'value': '1-02-02 Early Modern History'},
     {'label': '1-02-03 Modern and Current History',
      'value': '1-02-03 Modern and Current History'},
     {'label': '1-02-04 History of Science',
      'value': '1-02-04 History of Science'}]},
   {'label': '1-03 Fine Arts, Music, Theatre and Media Studies',
    'value': '1-03 Fine Arts, Music, Theatre and Media Studies',
    'children': [{'label': '1-03-01 Art History',
      'value': '1-03-01 Art History'},
     {'label': '1-03-02 Musicology', 'value': '1-03-02 Musicology'},
     {'label': '1-03-03 Theatre and Media Studies',
      'value': '1-03-03 Theatre and Media Studies'}]},
   {'label': '1-04 Linguistics',
    'value': '1-04 Linguistics',
    'children': [{'label': '1-04-01 General and Applied Linguistics',
      'value': '1-04-01 General and Applied Linguistics'},
     {'label': '1-04-02 Individual Linguistics',
      'value': '1-04-02 Individual Linguistics'},
     {'label': '1-04-03 Typology, Non-European Languages, Historical Linguistics',
      'value': '1-04-03 Typology, Non-European Languages, Historical Linguistics'}]},
   {'label': '1-05 Literary Studies',
    'value': '1-05 Literary Studies',
    'children': [{'label': '1-05-01 Medieval German Literature',
      'value': '1-05-01 Medieval German Literature'},
     {'label': '1-05-02 Modern German Literature',
      'value': '1-05-02 Modern German Literature'},
     {'label': '1-05-03 European and American Literature',
      'value': '1-05-03 European and American Literature'},
     {'label': '1-05-04 General and Comparative Literature and Cultural Studies',
      'value': '1-05-04 General and Comparative Literature and Cultural Studies'}]},
   {'label': '1-06 Non-European Languages and Cultures, Social and Cultural Anthropology, Jewish Studies and Religious Studies',
    'value': '1-06 Non-European Languages and Cultures, Social and Cultural Anthropology, Jewish Studies and Religious Studies',
    'children': [{'label': '1-06-01 Social and Cultural Anthropology and Ethnology/Folklore',
      'value': '1-06-01 Social and Cultural Anthropology and Ethnology/Folklore'},
     {'label': '1-06-02 Asian Studies', 'value': '1-06-02 Asian Studies'},
     {'label': '1-06-03 African, American and Oceania Studies',
      'value': '1-06-03 African, American and Oceania Studies'},
     {'label': '1-06-04 Islamic Studies, Arabian Studies, Semitic Studies',
      'value': '1-06-04 Islamic Studies, Arabian Studies, Semitic Studies'},
     {'label': '1-06-05 Religious Studies and Jewish Studies',
      'value': '1-06-05 Religious Studies and Jewish Studies'}]},
   {'label': '1-07 Theology',
    'value': '1-07 Theology',
    'children': [{'label': '1-07-01 Protestant Theology',
      'value': '1-07-01 Protestant Theology'},
     {'label': '1-07-02 Roman Catholic Theology',
      'value': '1-07-02 Roman Catholic Theology'}]},
   {'label': '1-08 Philosophy',
    'value': '1-08 Philosophy',
    'children': [{'label': '1-08-01 History of Philosophy',
      'value': '1-08-01 History of Philosophy'}]},
   {'label': '1-09 Education Sciences',
    'value': '1-09 Education Sciences',
    'children': [{'label': '1-09-01 General Education and History of Education',
      'value': '1-09-01 General Education and History of Education'},
     {'label': '1-09-02 Research on Teaching, Learning and Training',
      'value': '1-09-02 Research on Teaching, Learning and Training'},
     {'label': '1-09-03 Research on Socialization and Educational Institutions and Professions',
      'value': '1-09-03 Research on Socialization and Educational Institutions and Professions'}]},
   {'label': '1-10 Psychology',
    'value': '1-10 Psychology',
    'children': [{'label': '1-10-01 General, Biological and Mathematical Psychology',
      'value': '1-10-01 General, Biological and Mathematical Psychology'},
     {'label': '1-10-02 Developmental and Educational Psychology',
      'value': '1-10-02 Developmental and Educational Psychology'},
     {'label': '1-10-03 Social Psychology, Industrial and Organisational Psychology',
      'value': '1-10-03 Social Psychology, Industrial and Organisational Psychology'},
     {'label': '1-10-04 Differential Psychology, Clinical Psychology, Medical Psychology, Methodology',
      'value': '1-10-04 Differential Psychology, Clinical Psychology, Medical Psychology, Methodology'}]},
   {'label': '1-11 Social Sciences',
    'value': '1-11 Social Sciences',
    'children': [{'label': '1-11-01 Sociological Theory',
      'value': '1-11-01 Sociological Theory'},
     {'label': '1-11-02 Empirical Social Research',
      'value': '1-11-02 Empirical Social Research'},
     {'label': '1-11-03 Communication Science',
      'value': '1-11-03 Communication Science'},
     {'label': '1-11-04 Political Science',
      'value': '1-11-04 Political Science'}]},
   {'label': '1-12 Economics',
    'value': '1-12 Economics',
    'children': [{'label': '1-12-01 Economic Theory',
      'value': '1-12-01 Economic Theory'},
     {'label': '1-12-02 Economic and Social Policy',
      'value': '1-12-02 Economic and Social Policy'},
     {'label': '1-12-03 Public Finance', 'value': '1-12-03 Public Finance'},
     {'label': '1-12-04 Business Administration',
      'value': '1-12-04 Business Administration'},
     {'label': '1-12-05 Statistics and Econometrics',
      'value': '1-12-05 Statistics and Econometrics'},
     {'label': '1-12-06 Economic and Social History',
      'value': '1-12-06 Economic and Social History'}]},
   {'label': '1-13 Jurisprudence',
    'value': '1-13 Jurisprudence',
    'children': [{'label': '1-13-01 Legal and Political Philosophy, Legal History, Legal Theory',
      'value': '1-13-01 Legal and Political Philosophy, Legal History, Legal Theory'},
     {'label': '1-13-02 Private Law', 'value': '1-13-02 Private Law'},
     {'label': '1-13-03 Public Law', 'value': '1-13-03 Public Law'},
     {'label': '1-13-04 Criminal Law and Law of Criminal Procedure',
      'value': '1-13-04 Criminal Law and Law of Criminal Procedure'},
     {'label': '1-13-05 Criminology', 'value': '1-13-05 Criminology'}]}]},
 {'label': '2 Agriculture, Forestry, Horticulture and Veterinary Medicine',
  'value': '2 Agriculture, Forestry, Horticulture and Veterinary Medicine',
  'children': [{'label': '2-01 Basic Biological and Medical Research',
    'value': '2-01 Basic Biological and Medical Research',
    'children': [{'label': '2-01-01 Biochemistry',
      'value': '2-01-01 Biochemistry'},
     {'label': '2-01-02 Biophysics', 'value': '2-01-02 Biophysics'},
     {'label': '2-01-03 Cell Biology', 'value': '2-01-03 Cell Biology'},
     {'label': '2-01-04 Structural Biology',
      'value': '2-01-04 Structural Biology'},
     {'label': '2-01-05 General Genetics',
      'value': '2-01-05 General Genetics'},
     {'label': '2-01-06 Developmental Biology',
      'value': '2-01-06 Developmental Biology'},
     {'label': '2-01-07 Bioinformatics and Theoretical Biology',
      'value': '2-01-07 Bioinformatics and Theoretical Biology'},
     {'label': '2-01-08 Anatomy', 'value': '2-01-08 Anatomy'}]},
   {'label': '2-02 Plant Sciences',
    'value': '2-02 Plant Sciences',
    'children': [{'label': '2-02-01 Plant Systematics and Evolution',
      'value': '2-02-01 Plant Systematics and Evolution'},
     {'label': '2-02-02 Plant Ecology and Ecosystem Analysis',
      'value': '2-02-02 Plant Ecology and Ecosystem Analysis'},
     {'label': '2-02-03 Inter-organismic Interactions of Plants',
      'value': '2-02-03 Inter-organismic Interactions of Plants'},
     {'label': '2-02-04 Plant Physiology',
      'value': '2-02-04 Plant Physiology'},
     {'label': '2-02-05 Plant Biochemistry and Biophysics',
      'value': '2-02-05 Plant Biochemistry and Biophysics'},
     {'label': '2-02-06 Plant Cell and Developmental Biology',
      'value': '2-02-06 Plant Cell and Developmental Biology'},
     {'label': '2-02-07 Plant Genetics', 'value': '2-02-07 Plant Genetics'}]},
   {'label': '2-03 Zoology',
    'value': '2-03 Zoology',
    'children': [{'label': '2-03-01 Systematics and Morphology',
      'value': '2-03-01 Systematics and Morphology'},
     {'label': '2-03-02 Evolution, Anthropology',
      'value': '2-03-02 Evolution, Anthropology'},
     {'label': '2-03-03 Animal Ecology, Biodiversity and Ecosystem Research',
      'value': '2-03-03 Animal Ecology, Biodiversity and Ecosystem Research'},
     {'label': '2-03-04 Sensory and Behavioural Biology',
      'value': '2-03-04 Sensory and Behavioural Biology'},
     {'label': '2-03-05 Biochemistry and Animal Physiology',
      'value': '2-03-05 Biochemistry and Animal Physiology'},
     {'label': '2-03-06 Animal Genetics, Cell and Developmental Biology',
      'value': '2-03-06 Animal Genetics, Cell and Developmental Biology'}]},
   {'label': '2-04 Microbiology, Virology and Immunology',
    'value': '2-04 Microbiology, Virology and Immunology',
    'children': [{'label': '2-04-01 Metabolism, Biochemistry and Genetics of Microorganisms',
      'value': '2-04-01 Metabolism, Biochemistry and Genetics of Microorganisms'},
     {'label': '2-04-02 Microbial Ecology and Applied Microbiology',
      'value': '2-04-02 Microbial Ecology and Applied Microbiology'},
     {'label': '2-04-03 Medical Microbiology, Molecular Infection Biology',
      'value': '2-04-03 Medical Microbiology, Molecular Infection Biology'},
     {'label': '2-04-04 Virology', 'value': '2-04-04 Virology'},
     {'label': '2-04-05 Immunology', 'value': '2-04-05 Immunology'}]},
   {'label': '2-05 Medicine',
    'value': '2-05 Medicine',
    'children': [{'label': '2-05-01 Epidemiology, Medical Biometry, Medical Informatics',
      'value': '2-05-01 Epidemiology, Medical Biometry, Medical Informatics'},
     {'label': '2-05-02 Public Health, Health Services Research, Social Medicine',
      'value': '2-05-02 Public Health, Health Services Research, Social Medicine'},
     {'label': '2-05-03 Human Genetics', 'value': '2-05-03 Human Genetics'},
     {'label': '2-05-04 Physiology', 'value': '2-05-04 Physiology'},
     {'label': '2-05-05 Nutritional Sciences',
      'value': '2-05-05 Nutritional Sciences'},
     {'label': '2-05-06 Pathology and Forensic Medicine',
      'value': '2-05-06 Pathology and Forensic Medicine'},
     {'label': '2-05-07 Clinical Chemistry and Pathobiochemistry',
      'value': '2-05-07 Clinical Chemistry and Pathobiochemistry'},
     {'label': '2-05-08 Pharmacy', 'value': '2-05-08 Pharmacy'},
     {'label': '2-05-09 Pharmacology', 'value': '2-05-09 Pharmacology'},
     {'label': '2-05-10 Toxicology and Occupational Medicine',
      'value': '2-05-10 Toxicology and Occupational Medicine'},
     {'label': '2-05-12 Cardiology, Angiology',
      'value': '2-05-12 Cardiology, Angiology'},
     {'label': '2-05-13 Pneumology, Clinical Infectiology Intensive Care Medicine',
      'value': '2-05-13 Pneumology, Clinical Infectiology Intensive Care Medicine'},
     {'label': '2-05-14 Hematology, Oncology, Transfusion Medicine',
      'value': '2-05-14 Hematology, Oncology, Transfusion Medicine'},
     {'label': '2-05-15 Gastroenterology, Metabolism',
      'value': '2-05-15 Gastroenterology, Metabolism'},
     {'label': '2-05-16 Nephrology', 'value': '2-05-16 Nephrology'},
     {'label': '2-05-17 Endocrinology, Diabetology',
      'value': '2-05-17 Endocrinology, Diabetology'},
     {'label': '2-05-18 Rheumatology, Clinical Immunology, Allergology',
      'value': '2-05-18 Rheumatology, Clinical Immunology, Allergology'},
     {'label': '2-05-19 Dermatology', 'value': '2-05-19 Dermatology'},
     {'label': '2-05-20 Pediatric and Adolescent Medicine',
      'value': '2-05-20 Pediatric and Adolescent Medicine'},
     {'label': '2-05-21 Gynaecology and Obstetrics',
      'value': '2-05-21 Gynaecology and Obstetrics'},
     {'label': '2-05-22 Reproductive Medicine/Biology',
      'value': '2-05-22 Reproductive Medicine/Biology'},
     {'label': '2-05-23 Urology', 'value': '2-05-23 Urology'},
     {'label': '2-05-24 Gerontology and Geriatric Medicine',
      'value': '2-05-24 Gerontology and Geriatric Medicine'},
     {'label': '2-05-26 Cardiothoracic Surgery',
      'value': '2-05-26 Cardiothoracic Surgery'},
     {'label': '2-05-27 Traumatology and Orthopaedics',
      'value': '2-05-27 Traumatology and Orthopaedics'},
     {'label': '2-05-28 Dentistry, Oral Surgery',
      'value': '2-05-28 Dentistry, Oral Surgery'},
     {'label': '2-05-30 Radiology and Nuclear Medicine',
      'value': '2-05-30 Radiology and Nuclear Medicine'},
     {'label': '2-05-31 Radiation Oncology and Radiobiology',
      'value': '2-05-31 Radiation Oncology and Radiobiology'},
     {'label': '2-05-32 Biomedical Technology and Medical Physics',
      'value': '2-05-32 Biomedical Technology and Medical Physics'}]},
   {'label': '2-06 Neurosciences',
    'value': '2-06 Neurosciences',
    'children': [{'label': '2-06-01 Molecular Neuroscience and Neurogenetics',
      'value': '2-06-01 Molecular Neuroscience and Neurogenetics'},
     {'label': '2-06-02 Cellular Neuroscience',
      'value': '2-06-02 Cellular Neuroscience'},
     {'label': '2-06-03 Developmental Neurobiology',
      'value': '2-06-03 Developmental Neurobiology'},
     {'label': '2-06-04 Systemic Neuroscience, Computational Neuroscience, Behaviour',
      'value': '2-06-04 Systemic Neuroscience, Computational Neuroscience, Behaviour'},
     {'label': '2-06-05 Comparative Neurobiology',
      'value': '2-06-05 Comparative Neurobiology'},
     {'label': '2-06-06 Cognitive Neuroscience and Neuroimaging',
      'value': '2-06-06 Cognitive Neuroscience and Neuroimaging'},
     {'label': '2-06-07 Molecular Neurology',
      'value': '2-06-07 Molecular Neurology'},
     {'label': '2-06-08 Clinical Neurosciences I - Neurology, Neurosurgery',
      'value': '2-06-08 Clinical Neurosciences I - Neurology, Neurosurgery'},
     {'label': '2-06-09 Biological Psychiatry',
      'value': '2-06-09 Biological Psychiatry'},
     {'label': '2-06-10 Clinical Neurosciences II - Psychotherapy, Psychosomatic Medicine',
      'value': '2-06-10 Clinical Neurosciences II - Psychotherapy, Psychosomatic Medicine'},
     {'label': '2-06-11 Clinical Neurosciences III - Ophthalmology',
      'value': '2-06-11 Clinical Neurosciences III - Ophthalmology'}]},
   {'label': '2-07 Agriculture, Forestry, Horticulture and Veterinary Medicine',
    'value': '2-07 Agriculture, Forestry, Horticulture and Veterinary Medicine',
    'children': [{'label': '2-07-01 Soil Sciences',
      'value': '2-07-01 Soil Sciences'},
     {'label': '2-07-02 Plant Cultivation',
      'value': '2-07-02 Plant Cultivation'},
     {'label': '2-07-03 Plant Nutrition', 'value': '2-07-03 Plant Nutrition'},
     {'label': '2-07-04 Ecology of Agricultural Landscapes',
      'value': '2-07-04 Ecology of Agricultural Landscapes'},
     {'label': '2-07-05 Plant Breeding', 'value': '2-07-05 Plant Breeding'},
     {'label': '2-07-07 Agricultural and Food Process Engineering',
      'value': '2-07-07 Agricultural and Food Process Engineering'},
     {'label': '2-07-08 Agricultural Economics and Sociology',
      'value': '2-07-08 Agricultural Economics and Sociology'},
     {'label': '2-07-09 Inventory Control and Use of Forest Resources',
      'value': '2-07-09 Inventory Control and Use of Forest Resources'},
     {'label': '2-07-10 Basic Forest Research',
      'value': '2-07-10 Basic Forest Research'},
     {'label': '2-07-11 Animal Husbandry, Breeding and Hygiene',
      'value': '2-07-11 Animal Husbandry, Breeding and Hygiene'},
     {'label': '2-07-13 Basic Veterinary Medical Science',
      'value': '2-07-13 Basic Veterinary Medical Science'},
     {'label': '2-07-14 Basic Research on Pathogenesis, Diagnostics and Therapy and Clinical Veterinary Medicine',
      'value': '2-07-14 Basic Research on Pathogenesis, Diagnostics and Therapy and Clinical Veterinary Medicine'}]}]},
 {'label': '3 Geosciences (including Geography)',
  'value': '3 Geosciences (including Geography)',
  'children': [{'label': '3-01 Molecular Chemistry',
    'value': '3-01 Molecular Chemistry',
    'children': [{'label': '3-01-01 Inorganic Molecular Chemistry',
      'value': '3-01-01 Inorganic Molecular Chemistry'},
     {'label': '3-01-02 Organic Molecular Chemistry',
      'value': '3-01-02 Organic Molecular Chemistry'}]},
   {'label': '3-02 Chemical Solid State and Surface Research',
    'value': '3-02 Chemical Solid State and Surface Research',
    'children': [{'label': '3-02-01 Solid State and Surface Chemistry, Material Synthesis',
      'value': '3-02-01 Solid State and Surface Chemistry, Material Synthesis'},
     {'label': '3-02-02 Physical Chemistry of Solids and Surfaces, Material Characterisation',
      'value': '3-02-02 Physical Chemistry of Solids and Surfaces, Material Characterisation'},
     {'label': '3-02-03 Theory and Modelling',
      'value': '3-02-03 Theory and Modelling'}]},
   {'label': '3-03 Physical and Theoretical Chemistry',
    'value': '3-03 Physical and Theoretical Chemistry',
    'children': [{'label': '3-03-01 Physical Chemistry of Molecules, Interfaces and Liquids - Spectroscopy, Kinetics',
      'value': '3-03-01 Physical Chemistry of Molecules, Interfaces and Liquids - Spectroscopy, Kinetics'},
     {'label': '3-03-02 General Theoretical Chemistry',
      'value': '3-03-02 General Theoretical Chemistry'}]},
   {'label': '3-04 Analytical Chemistry, Method Development (Chemistry)',
    'value': '3-04 Analytical Chemistry, Method Development (Chemistry)',
    'children': [{'label': '3-04-01 Analytical Chemistry, Method Development (Chemistry)',
      'value': '3-04-01 Analytical Chemistry, Method Development (Chemistry)'}]},
   {'label': '3-05 Biological Chemistry and Food Chemistry',
    'value': '3-05 Biological Chemistry and Food Chemistry',
    'children': [{'label': '3-05-01 Biological and Biomimetic Chemistry',
      'value': '3-05-01 Biological and Biomimetic Chemistry'},
     {'label': '3-05-02 Food Chemistry', 'value': '3-05-02 Food Chemistry'}]},
   {'label': '3-06 Polymer Research',
    'value': '3-06 Polymer Research',
    'children': [{'label': '3-06-01 Preparatory and Physical Chemistry of Polymers',
      'value': '3-06-01 Preparatory and Physical Chemistry of Polymers'},
     {'label': '3-06-02 Experimental and Theoretical Physics of Polymers',
      'value': '3-06-02 Experimental and Theoretical Physics of Polymers'},
     {'label': '3-06-03 Polymer Materials',
      'value': '3-06-03 Polymer Materials'}]},
   {'label': '3-07 Condensed Matter Physics',
    'value': '3-07 Condensed Matter Physics',
    'children': [{'label': '3-07-01 Experimental Condensed Matter Physics',
      'value': '3-07-01 Experimental Condensed Matter Physics'},
     {'label': '3-07-02 Theoretical Condensed Matter Physics',
      'value': '3-07-02 Theoretical Condensed Matter Physics'}]},
   {'label': '3-08 Optics, Quantum Optics and Physics of Atoms, Molecules and Plasmas',
    'value': '3-08 Optics, Quantum Optics and Physics of Atoms, Molecules and Plasmas',
    'children': [{'label': '3-08-01 Optics, Quantum Optics, Atoms, Molecules, Plasmas',
      'value': '3-08-01 Optics, Quantum Optics, Atoms, Molecules, Plasmas'}]},
   {'label': '3-09 Particles, Nuclei and Fields',
    'value': '3-09 Particles, Nuclei and Fields',
    'children': [{'label': '3-09-01 Particles, Nuclei and Fields',
      'value': '3-09-01 Particles, Nuclei and Fields'}]},
   {'label': '3-10 Statistical Physics, Soft Matter, Biological Physics, Nonlinear Dynamics',
    'value': '3-10 Statistical Physics, Soft Matter, Biological Physics, Nonlinear Dynamics',
    'children': [{'label': '3-10-01 Statistical Physics, Soft Matter, Biological Physics, Nonlinear Dynamics',
      'value': '3-10-01 Statistical Physics, Soft Matter, Biological Physics, Nonlinear Dynamics'}]},
   {'label': '3-11 Astrophysics and Astronomy',
    'value': '3-11 Astrophysics and Astronomy',
    'children': [{'label': '3-11-01 Astrophysics and Astronomy',
      'value': '3-11-01 Astrophysics and Astronomy'}]},
   {'label': '3-12 Mathematics',
    'value': '3-12 Mathematics',
    'children': [{'label': '3-12-01 Mathematics',
      'value': '3-12-01 Mathematics'}]},
   {'label': '3-13 Atmospheric Science and Oceanography',
    'value': '3-13 Atmospheric Science and Oceanography',
    'children': [{'label': '3-13-01 Atmospheric Science',
      'value': '3-13-01 Atmospheric Science'},
     {'label': '3-13-02 Oceanography', 'value': '3-13-02 Oceanography'}]},
   {'label': '3-14 Geology and Palaeontology',
    'value': '3-14 Geology and Palaeontology',
    'children': [{'label': '3-14-01 Geology and Palaeontology',
      'value': '3-14-01 Geology and Palaeontology'}]},
   {'label': '3-15 Geophysics and Geodesy',
    'value': '3-15 Geophysics and Geodesy',
    'children': [{'label': '3-15-01 Geophysics',
      'value': '3-15-01 Geophysics'},
     {'label': '3-15-02 Geodesy, Photogrammetry, Remote Sensing, Geoinformatics, Cartogaphy',
      'value': '3-15-02 Geodesy, Photogrammetry, Remote Sensing, Geoinformatics, Cartogaphy'}]},
   {'label': '3-16 Geochemistry, Mineralogy and Crystallography',
    'value': '3-16 Geochemistry, Mineralogy and Crystallography',
    'children': [{'label': '3-16-01 Geochemistry, Mineralogy and Crystallography',
      'value': '3-16-01 Geochemistry, Mineralogy and Crystallography'}]},
   {'label': '3-17 Geography',
    'value': '3-17 Geography',
    'children': [{'label': '3-17-01 Physical Geography',
      'value': '3-17-01 Physical Geography'},
     {'label': '3-17-02 Human Geography',
      'value': '3-17-02 Human Geography'}]},
   {'label': '3-18 Water Research',
    'value': '3-18 Water Research',
    'children': [{'label': '3-18-01 Hydrogeology, Hydrology, Limnology, Urban Water Management, Water Chemistry, Integrated Water Resources Management',
      'value': '3-18-01 Hydrogeology, Hydrology, Limnology, Urban Water Management, Water Chemistry, Integrated Water Resources Management'}]}]},
 {'label': '4 Construction Engineering and Architecture',
  'value': '4 Construction Engineering and Architecture',
  'children': [{'label': '4-01 Production Technology',
    'value': '4-01 Production Technology',
    'children': [{'label': '4-01-05 Production Automation, Factory Operation, Operations Manangement',
      'value': '4-01-05 Production Automation, Factory Operation, Operations Manangement'}]},
   {'label': '4-02 Mechanics and Constructive Mechanical Engineering',
    'value': '4-02 Mechanics and Constructive Mechanical Engineering',
    'children': [{'label': '4-02-04 Acoustics',
      'value': '4-02-04 Acoustics'}]},
   {'label': '4-03 Process Engineering, Technical Chemistry',
    'value': '4-03 Process Engineering, Technical Chemistry',
    'children': [{'label': '4-03-01 Chemical and Thermal Process Engineering',
      'value': '4-03-01 Chemical and Thermal Process Engineering'},
     {'label': '4-03-02 Technical Chemistry',
      'value': '4-03-02 Technical Chemistry'},
     {'label': '4-03-04 Biological Process Engineering',
      'value': '4-03-04 Biological Process Engineering'}]},
   {'label': '4-04 Heat Energy Technology, Thermal Machines, Fluid Mechanics',
    'value': '4-04 Heat Energy Technology, Thermal Machines, Fluid Mechanics',
    'children': [{'label': '4-04-01 Energy Process Engineering',
      'value': '4-04-01 Energy Process Engineering'},
     {'label': '4-04-02 Technical Thermodynamics',
      'value': '4-04-02 Technical Thermodynamics'}]},
   {'label': '4-05 Materials Engineering',
    'value': '4-05 Materials Engineering',
    'children': [{'label': '4-05-01 Metallurgical and Thermal Processes, Thermomechanical Treatment of Materials',
      'value': '4-05-01 Metallurgical and Thermal Processes, Thermomechanical Treatment of Materials'},
     {'label': '4-05-02 Sintered Metallic and Ceramic Materials',
      'value': '4-05-02 Sintered Metallic and Ceramic Materials'},
     {'label': '4-05-03 Composite Materials',
      'value': '4-05-03 Composite Materials'},
     {'label': '4-05-05 Coating and Surface Technology',
      'value': '4-05-05 Coating and Surface Technology'}]},
   {'label': '4-06 Materials Science',
    'value': '4-06 Materials Science',
    'children': [{'label': '4-06-01 Thermodynamics and Kinetics of Materials',
      'value': '4-06-01 Thermodynamics and Kinetics of Materials'},
     {'label': '4-06-02 Synthesis and Properties of Functional Materials',
      'value': '4-06-02 Synthesis and Properties of Functional Materials'},
     {'label': '4-06-03 Microstructural Mechanical Properties of Materials',
      'value': '4-06-03 Microstructural Mechanical Properties of Materials'},
     {'label': '4-06-04 Structuring and Functionalisation',
      'value': '4-06-04 Structuring and Functionalisation'},
     {'label': '4-06-05 Biomaterials', 'value': '4-06-05 Biomaterials'}]},
   {'label': '4-07 Systems Engineering',
    'value': '4-07 Systems Engineering',
    'children': [{'label': '4-07-01 Automation, Control Systems, Robotics, Mechatronics',
      'value': '4-07-01 Automation, Control Systems, Robotics, Mechatronics'},
     {'label': '4-07-02 Measurement Systems',
      'value': '4-07-02 Measurement Systems'},
     {'label': '4-07-04 Traffic and Transport Systems, Logistics',
      'value': '4-07-04 Traffic and Transport Systems, Logistics'},
     {'label': '4-07-05 Human Factors, Ergonomics, Human-Machine Systems',
      'value': '4-07-05 Human Factors, Ergonomics, Human-Machine Systems'}]},
   {'label': '4-08 Electrical Engineering',
    'value': '4-08 Electrical Engineering',
    'children': [{'label': '4-08-01 Electronic Semiconductors, Components, Circuits, Systems',
      'value': '4-08-01 Electronic Semiconductors, Components, Circuits, Systems'},
     {'label': '4-08-02 Communication, High-Frequency and Network Technology, Theoretical Electrical Engineering',
      'value': '4-08-02 Communication, High-Frequency and Network Technology, Theoretical Electrical Engineering'},
     {'label': '4-08-03 Electrical Energy Generation, Distribution, Application',
      'value': '4-08-03 Electrical Energy Generation, Distribution, Application'}]},
   {'label': '4-09 Computer Science',
    'value': '4-09 Computer Science',
    'children': [{'label': '4-09-01 Theoretical Computer Science',
      'value': '4-09-01 Theoretical Computer Science'},
     {'label': '4-09-02 Software Technology',
      'value': '4-09-02 Software Technology'},
     {'label': '4-09-03 Operating, Communication and Information Systems',
      'value': '4-09-03 Operating, Communication and Information Systems'},
     {'label': '4-09-04 Artificial Intelligence, Image and Language Processing',
      'value': '4-09-04 Artificial Intelligence, Image and Language Processing'}]},
   {'label': '4-10 Construction Engineering and Architecture',
    'value': '4-10 Construction Engineering and Architecture',
    'children': [{'label': '4-10-01 Architecture, Building and Construction History, Sustainable Building Technology, Building Design',
      'value': '4-10-01 Architecture, Building and Construction History, Sustainable Building Technology, Building Design'},
     {'label': '4-10-02 Urbanism, Spatial Planning, Transportation and Infrastructure Planning, Landscape Planning',
      'value': '4-10-02 Urbanism, Spatial Planning, Transportation and Infrastructure Planning, Landscape Planning'},
     {'label': '4-10-04 Sructural Engineering, Building Informatics, Construction Operation',
      'value': '4-10-04 Sructural Engineering, Building Informatics, Construction Operation'},
     {'label': '4-10-06 Geotechnics, Hydraulic Engineering',
      'value': '4-10-06 Geotechnics, Hydraulic Engineering'}]}]}]
    # Note: The structure above is for illustration purposes. To reach approximately 200 nodes, you would need to further expand each folder and sub-folder accordingly.


    return_select = tree_select(nodes)
    st.write(return_select)


#######################
# Plots

# Heatmap
def make_heatmap(input_df, input_y, input_x, input_color, input_color_theme):
    heatmap = alt.Chart(input_df).mark_rect().encode(
            y=alt.Y(f'{input_y}:O', axis=alt.Axis(title="Year", titleFontSize=18, titlePadding=15, titleFontWeight=900, labelAngle=0)),
            x=alt.X(f'{input_x}:O', axis=alt.Axis(title="", titleFontSize=18, titlePadding=15, titleFontWeight=900)),
            color=alt.Color(f'max({input_color}):Q',
                             legend=None,
                             scale=alt.Scale(scheme=input_color_theme)),
            stroke=alt.value('black'),
            strokeWidth=alt.value(0.25),
        ).properties(width=900
        ).configure_axis(
        labelFontSize=12,
        titleFontSize=12
        ) 
    # height=300
    return heatmap

# Choropleth map

def make_choropleth(input_df, input_id, input_column, input_color_theme):
    selected_color_theme = "blues"
    selected_year = 2018
    choropleth = px.choropleth(input_df, locations=input_id, color=input_column, locationmode="USA-states",
                               color_continuous_scale=input_color_theme,
                               range_color=(0, max(df_selected_year.population)),
                               scope="usa",
                               labels={'population':'Population'}
                              )
    choropleth.update_layout(
        template='plotly_dark',
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0)',
        margin=dict(l=0, r=0, t=0, b=0),
        height=350
    )
    return choropleth


# Donut chart
def make_donut(input_response, input_text, input_color):
  if input_color == 'blue':
      chart_color = ['#29b5e8', '#155F7A']
  if input_color == 'green':
      chart_color = ['#27AE60', '#12783D']
  if input_color == 'orange':
      chart_color = ['#F39C12', '#875A12']
  if input_color == 'red':
      chart_color = ['#E74C3C', '#781F16']
    
  source = pd.DataFrame({
      "Topic": ['', input_text],
      "% value": [100-input_response, input_response]
  })
  source_bg = pd.DataFrame({
      "Topic": ['', input_text],
      "% value": [100, 0]
  })
    
  plot = alt.Chart(source).mark_arc(innerRadius=45, cornerRadius=25).encode(
      theta="% value",
      color= alt.Color("Topic:N",
                      scale=alt.Scale(
                          #domain=['A', 'B'],
                          domain=[input_text, ''],
                          # range=['#29b5e8', '#155F7A']),  # 31333F
                          range=chart_color),
                      legend=None),
  ).properties(width=130, height=130)
    
  text = plot.mark_text(align='center', color="#29b5e8", font="Lato", fontSize=32, fontWeight=700, fontStyle="italic").encode(text=alt.value(f'{input_response} %'))
  plot_bg = alt.Chart(source_bg).mark_arc(innerRadius=45, cornerRadius=20).encode(
      theta="% value",
      color= alt.Color("Topic:N",
                      scale=alt.Scale(
                          # domain=['A', 'B'],
                          domain=[input_text, ''],
                          range=chart_color),  # 31333F
                      legend=None),
  ).properties(width=130, height=130)
  return plot_bg + plot + text

# Convert population to text 
def format_number(num):
    if num > 1000000:
        if not num % 1000000:
            return f'{num // 1000000} M'
        return f'{round(num / 1000000, 1)} M'
    return f'{num // 1000} K'

# Calculation year-over-year population migrations
def calculate_population_difference(input_df, input_year):
  selected_year_data = input_df[input_df['year'] == input_year].reset_index()
  previous_year_data = input_df[input_df['year'] == input_year - 1].reset_index()
  selected_year_data['population_difference'] = selected_year_data.population.sub(previous_year_data.population, fill_value=0)
  return pd.concat([selected_year_data.states, selected_year_data.id, selected_year_data.population, selected_year_data.population_difference], axis=1).sort_values(by="population_difference", ascending=False)


#######################
# Dashboard Main Panel
col = st.columns((1.5, 4.5), gap='medium')

with col[0]:
    st.markdown('#### Gains/Losses')

    selected_color_theme = "blues"
    selected_year = 2018
    df_population_difference_sorted = calculate_population_difference(df_reshaped, selected_year)

    if selected_year > 2010:
        first_state_name = df_population_difference_sorted.states.iloc[0]
        first_state_population = format_number(df_population_difference_sorted.population.iloc[0])
        first_state_delta = format_number(df_population_difference_sorted.population_difference.iloc[0])
    else:
        first_state_name = '-'
        first_state_population = '-'
        first_state_delta = ''
    st.metric(label=first_state_name, value=first_state_population, delta=first_state_delta)

    if selected_year > 2010:
        last_state_name = df_population_difference_sorted.states.iloc[-1]
        last_state_population = format_number(df_population_difference_sorted.population.iloc[-1])   
        last_state_delta = format_number(df_population_difference_sorted.population_difference.iloc[-1])   
    else:
        last_state_name = '-'
        last_state_population = '-'
        last_state_delta = ''
    st.metric(label=last_state_name, value=last_state_population, delta=last_state_delta)

    
    st.markdown('#### States Migration')

    if selected_year > 2010:
        # Filter states with population difference > 50000
        # df_greater_50000 = df_population_difference_sorted[df_population_difference_sorted.population_difference_absolute > 50000]
        df_greater_50000 = df_population_difference_sorted[df_population_difference_sorted.population_difference > 50000]
        df_less_50000 = df_population_difference_sorted[df_population_difference_sorted.population_difference < -50000]
        
        # % of States with population difference > 50000
        states_migration_greater = round((len(df_greater_50000)/df_population_difference_sorted.states.nunique())*100)
        states_migration_less = round((len(df_less_50000)/df_population_difference_sorted.states.nunique())*100)
        donut_chart_greater = make_donut(states_migration_greater, 'Inbound Migration', 'green')
        donut_chart_less = make_donut(states_migration_less, 'Outbound Migration', 'red')
    else:
        states_migration_greater = 0
        states_migration_less = 0
        donut_chart_greater = make_donut(states_migration_greater, 'Inbound Migration', 'green')
        donut_chart_less = make_donut(states_migration_less, 'Outbound Migration', 'red')

    migrations_col = st.columns((0.2, 1, 0.2))
    with migrations_col[1]:
        st.write('Inbound')
        st.altair_chart(donut_chart_greater)
        st.write('Outbound')
        st.altair_chart(donut_chart_less)

with col[1]:
    st.markdown('#### Selected Data')
    
    #choropleth = make_choropleth(df_selected_year, 'states_code', 'population', selected_color_theme)
    #st.plotly_chart(choropleth, use_container_width=True)
    
    #heatmap = make_heatmap(df_reshaped, 'year', 'states', 'population', selected_color_theme)
    #st.altair_chart(heatmap, use_container_width=True)
    
    st.dataframe(pd_grouped, use_container_width=True)