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
#selected_color_theme = "blues"
#selected_year = 2018

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




#######################
### re3data stuff






#######################

# Sidebar
with st.sidebar:
    #st.title('🏂 US Population Dashboard')
    st.title("🐙 Streamlit-tree-select")
    st.subheader("A simple and elegant checkbox tree for Streamlit.")

    st.metric(label="# of selected repos:", value=pd_parsed.shape[0], delta=(3216-pd_parsed.shape[0]))

    # Create nodes to display
    nodes = [
        {"label": "Folder A", "value": "folder_a"},
        {
            "label": "Folder B",
            "value": "folder_b",
            "children": [
                {"label": "Sub-folder A", "value": "sub_a"},
                {"label": "Sub-folder B", "value": "sub_b"},
                {"label": "Sub-folder C", "value": "sub_c"},
                {
                    "label": "Sub-folder D",
                    "value": "sub_d",
                    "children": [
                        {"label": "Sub-sub-folder A", "value": "sub_sub_a"},
                        {"label": "Sub-sub-folder B", "value": "sub_sub_b"},
                        {"label": "Sub-sub-folder C", "value": "sub_sub_c"},
                        {"label": "Sub-sub-folder D", "value": "sub_sub_d"},
                        {"label": "Sub-sub-folder E", "value": "sub_sub_e"},
                    ],
                },
                {"label": "Sub-folder E", "value": "sub_e"},
                {"label": "Sub-folder F", "value": "sub_f"},
            ],
        },
        {
            "label": "Folder C",
            "value": "folder_c",
            "children": [
                {"label": "Sub-folder G", "value": "sub_g"},
                {"label": "Sub-folder H", "value": "sub_h"},
                {
                    "label": "Sub-folder I",
                    "value": "sub_i",
                    "children": [
                        {"label": "Sub-sub-folder F", "value": "sub_sub_f"},
                        {"label": "Sub-sub-folder G", "value": "sub_sub_g"},
                        {"label": "Sub-sub-folder H", "value": "sub_sub_h"},
                        {
                            "label": "Sub-sub-folder I",
                            "value": "sub_sub_i",
                            "children": [
                                {"label": "Sub-sub-sub-folder A", "value": "sub_sub_sub_a"},
                                {"label": "Sub-sub-sub-folder B", "value": "sub_sub_sub_b"},
                                {"label": "Sub-sub-sub-folder C", "value": "sub_sub_sub_c"},
                            ],
                        },
                        {"label": "Sub-sub-folder J", "value": "sub_sub_j"},
                    ],
                },
                {
                    "label": "Sub-folder J",
                    "value": "sub_j",
                    "children": [
                        {"label": "Sub-sub-folder K", "value": "sub_sub_k"},
                        {"label": "Sub-sub-folder L", "value": "sub_sub_l"},
                        {"label": "Sub-sub-folder M", "value": "sub_sub_m"},
                    ],
                },
                {"label": "Sub-folder K", "value": "sub_k"},
            ],
        },
        {
            "label": "Folder D",
            "value": "folder_d",
            "children": [
                {"label": "Sub-folder L", "value": "sub_l"},
                {"label": "Sub-folder M", "value": "sub_m"},
                {"label": "Sub-folder N", "value": "sub_n"},
                {
                    "label": "Sub-folder O",
                    "value": "sub_o",
                    "children": [
                        {"label": "Sub-sub-folder N", "value": "sub_sub_n"},
                        {"label": "Sub-sub-folder O", "value": "sub_sub_o"},
                        {"label": "Sub-sub-folder P", "value": "sub_sub_p"},
                        {"label": "Sub-sub-folder Q", "value": "sub_sub_q"},
                    ],
                },
                {"label": "Sub-folder P", "value": "sub_p"},
            ],
        },
        {
            "label": "Folder E",
            "value": "folder_e",
            "children": [
                {"label": "Sub-folder Q", "value": "sub_q"},
                {"label": "Sub-folder R", "value": "sub_r"},
                {"label": "Sub-folder S", "value": "sub_s"},
                {
                    "label": "Sub-folder T",
                    "value": "sub_t",
                    "children": [
                        {"label": "Sub-sub-folder R", "value": "sub_sub_r"},
                        {"label": "Sub-sub-folder S", "value": "sub_sub_s"},
                        {"label": "Sub-sub-folder T", "value": "sub_sub_t"},
                        {"label": "Sub-sub-folder U", "value": "sub_sub_u"},
                        {"label": "Sub-sub-folder V", "value": "sub_sub_v"},
                    ],
                },
                {
                    "label": "Sub-folder U",
                    "value": "sub_u",
                    "children": [
                        {"label": "Sub-sub-folder W", "value": "sub_sub_w"},
                        {"label": "Sub-sub-folder X", "value": "sub_sub_x"},
                        {"label": "Sub-sub-folder Y", "value": "sub_sub_y"},
                    ],
                },
            ],
        },
        # Add more folders and sub-folders to reach approximately 200 nodes
        {
            "label": "Folder F",
            "value": "folder_f",
            "children": [
                {"label": "Sub-folder V", "value": "sub_v"},
                {"label": "Sub-folder W", "value": "sub_w"},
                {"label": "Sub-folder X", "value": "sub_x"},
                {
                    "label": "Sub-folder Y",
                    "value": "sub_y",
                    "children": [
                        {"label": "Sub-sub-folder Z", "value": "sub_sub_z"},
                        {"label": "Sub-sub-folder AA", "value": "sub_sub_aa"},
                        {"label": "Sub-sub-folder BB", "value": "sub_sub_bb"},
                    ],
                },
                {"label": "Sub-folder Z", "value": "sub_z"},
            ],
        },
        {
            "label": "Folder G",
            "value": "folder_g",
            "children": [
                {"label": "Sub-folder AA", "value": "sub_aa"},
                {"label": "Sub-folder BB", "value": "sub_bb"},
                {"label": "Sub-folder CC", "value": "sub_cc"},
                {
                    "label": "Sub-folder DD",
                    "value": "sub_dd",
                    "children": [
                        {"label": "Sub-sub-folder EE", "value": "sub_sub_ee"},
                        {"label": "Sub-sub-folder FF", "value": "sub_sub_ff"},
                        {"label": "Sub-sub-folder GG", "value": "sub_sub_gg"},
                    ],
                },
                {"label": "Sub-folder EE", "value": "sub_ee"},
            ],
        },
        {
            "label": "Folder H",
            "value": "folder_h",
            "children": [
                {"label": "Sub-folder FF", "value": "sub_ff"},
                {"label": "Sub-folder GG", "value": "sub_gg"},
                {"label": "Sub-folder HH", "value": "sub_hh"},
                {
                    "label": "Sub-folder II",
                    "value": "sub_ii",
                    "children": [
                        {"label": "Sub-sub-folder JJ", "value": "sub_sub_jj"},
                        {"label": "Sub-sub-folder KK", "value": "sub_sub_kk"},
                        {"label": "Sub-sub-folder LL", "value": "sub_sub_ll"},
                    ],
                },
                {"label": "Sub-folder JJ", "value": "sub_jj"},
            ],
        },
        {
            "label": "Folder I",
            "value": "folder_i",
            "children": [
                {"label": "Sub-folder KK", "value": "sub_kk"},
                {"label": "Sub-folder LL", "value": "sub_ll"},
                {"label": "Sub-folder MM", "value": "sub_mm"},
                {
                    "label": "Sub-folder NN",
                    "value": "sub_nn",
                    "children": [
                        {"label": "Sub-sub-folder OO", "value": "sub_sub_oo"},
                        {"label": "Sub-sub-folder PP", "value": "sub_sub_pp"},
                        {"label": "Sub-sub-folder QQ", "value": "sub_sub_qq"},
                    ],
                },
                {"label": "Sub-folder OO", "value": "sub_oo"},
            ],
        },
        {
            "label": "Folder J",
            "value": "folder_j",
            "children": [
                {"label": "Sub-folder PP", "value": "sub_pp"},
                {"label": "Sub-folder QQ", "value": "sub_qq"},
                {"label": "Sub-folder RR", "value": "sub_rr"},
                {
                    "label": "Sub-folder SS",
                    "value": "sub_ss",
                    "children": [
                        {"label": "Sub-sub-folder TT", "value": "sub_sub_tt"},
                        {"label": "Sub-sub-folder UU", "value": "sub_sub_uu"},
                        {"label": "Sub-sub-folder VV", "value": "sub_sub_vv"},
                    ],
                },
                {"label": "Sub-folder TT", "value": "sub_tt"},
            ],
        },
    ]

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
    st.markdown('#### Total Population')
    
    choropleth = make_choropleth(df_selected_year, 'states_code', 'population', selected_color_theme)
    st.plotly_chart(choropleth, use_container_width=True)
    
    heatmap = make_heatmap(df_reshaped, 'year', 'states', 'population', selected_color_theme)
    st.altair_chart(heatmap, use_container_width=True)
    
