import pandas as pd
import numpy as np
import pydeck as pdk
import streamlit as st
import matplotlib.pyplot as plt
from streamlit_option_menu import option_menu


def loadData():
    df = pd.read_csv('boston_building_violations_7000_sample.csv',
                     header=0,
                     names=['Case Number', 'Date/Time', 'Status', 'Code', 'Value', 'Violation Type', 'violation_stno',
                            'violation_sthigh', 'Street Name', 'Street Suffix', 'City', 'State', 'Zip Code', 'Ward',
                            'Contact Address', 'Second Contact Address', 'Contact City', 'Contact State',
                            'Contact Zip', 'sam_id', 'Latitude', 'Longitude', 'Location'],
                     index_col='Case Number')

    # Clean the data by removing rows with NaN values in 'Violation Type'
    df_cleaned = cleanData(df)

    # Split 'Date/Time' into 'Date' and 'Time'
    df_cleaned[['Date', 'Time']] = df_cleaned['Date/Time'].str.split(' ', expand=True)

    return df_cleaned


def cleanData(df):
    # Remove rows with NaN values in 'Violation Type'
    df_cleaned = df.dropna(subset=['Violation Type'])

    # Drop rows with NaN values in 'City' column
    df_cleaned = df_cleaned.dropna(subset=['City'])

    # Drop rows with NaN values in 'Status' column
    df_cleaned = df_cleaned.dropna(subset=['Status'])

    df_cleaned = df_cleaned[df_cleaned['Violation Type'] != "."]

    # Makes sure the suffix read St not ST or Ave not AVE
    df_cleaned['Street Suffix'] = df_cleaned['Street Suffix'].str.title()

    return df_cleaned


def calculate_city_statistics(df, selected_city='Boston'):
    # Calculate and return statistics related to violations in the selected city.
    city_df = df[df['City'] == selected_city]

    totalViolations = len(city_df)
    openViolations = len(city_df[city_df['Status'] == 'Open'])
    closedViolations = len(city_df[city_df['Status'] == 'Closed'])

    most_frequent_type = city_df['Violation Type'].mode().values[0]
    most_frequent_count = city_df['Violation Type'].value_counts().max()

    return totalViolations, openViolations, closedViolations, most_frequent_type, most_frequent_count


def homePage():
    # Create a container to add header and subheaders
    with st.container():
        st.header("Exploring Boston's Building Safety: A Data-Driven Journey")
        st.subheader("This web-based Python application analyzes the violations "
                     "on Boston buildings or properties issued by inspectors from the Building and "
                     "Structures Division of the Inspectional Services Department.")

        # Adding image that's the size of the container width
        st.image("boston_skyline.jpg", use_column_width=True)


def page1(df):
    # This page layers a scatterplot over a map
    # I used the pydeck library - see here (https://docs.streamlit.io/library/api-reference/charts/st.pydeck_chart)
    # I wanted to use a more detailed map, so I used pyDeck
    # For a cool map style I referred to github where I learned how to use
    # mapbox map styles - see here: (https://github.com/streamlit/streamlit/pull/5074)

    df['Location'] = df['Location'].apply(eval)
    st.header("Map of Building Violations by City/Region")

    city = st.selectbox("Select City", sorted(df['City'].dropna().unique()))
    df_filtered = df[df['City'] == city].dropna(subset=['Latitude', 'Longitude'])
    total_violations = len(df_filtered)

    if not df_filtered.empty:
        # Use of pandas.unique() to get unique values
        violationTypes = df_filtered['Violation Type'].unique()
        # list comprehension to get random to colors to data points based on violation types and uses
        violationColorDict = {violation: [np.random.randint(0, 256) for i in range(3)] for violation in
                            violationTypes}

        # creates a new column named 'Color' in the df df_filtered
        # using the lists of three random integers generated based on the 'Violation Type' column
        df_filtered['Color'] = df_filtered['Violation Type'].map(violationColorDict)

        selectedType = st.selectbox("Select Violation Type",
                                               ['All'] + list(sorted(df_filtered['Violation Type'].unique())))
        if selectedType != 'All':
            df_filtered = df_filtered[df_filtered['Violation Type'] == selectedType]

        scatterplot = pdk.Layer(
            "ScatterplotLayer",
            data=df_filtered,
            get_position=["Longitude", "Latitude"],
            get_color="[Color[0], Color[1], Color[2], 255]",
            get_radius=30,
        )

        view = pdk.ViewState(
            longitude=df_filtered['Longitude'].mean(),
            latitude=df_filtered['Latitude'].mean(),
            zoom=13
        )

        deck = pdk.Deck(
            map_style="mapbox://styles/mapbox/light-v9",
            layers=[scatterplot],
            initial_view_state=view,
        )

        st.pydeck_chart(deck)

        # Display count of total violations and selected violation type

        if selectedType == "All":
            st.info(f"Total Violations in {city}: {total_violations}")
        else:
            df_copy = df[df['City'] == city].dropna(subset=['Latitude', 'Longitude'])
            selected_type_df = df_copy[df_copy['Violation Type'] == selectedType]
            selected_type_count = len(selected_type_df)
            st.info(f"Total Violations in {city}: {total_violations}")
            st.info(f"'{selectedType}': {selected_type_count}")
            on = st.toggle('See Violation Street Names')

            if on:
                st.write(f"'{selectedType}' violations occur on the following streets in {city}:")
                # Concatenate 'Street Name' and 'Street Suffix' with a space
                streetName = selected_type_df['Street Name'] + ' ' + selected_type_df['Street Suffix']
                # Get unique street names
                unique_streetNames = streetName.unique()
                # Convert to a list to avoid displaying the index
                street_names_list = unique_streetNames.tolist()
                # Display each unique street name on a new line using Markdown formatting
                for street in street_names_list:
                    st.markdown(f"- {street}")
    else:
        st.warning("No data available for the selected city.")


def page2(df):
    # This page displays the top 10 violation types in Boston using a bar chart
    st.header("Top Violation Types in Boston, MA")

    # Bar chart to show the top 10 violation types
    counts = df['Violation Type'].value_counts()
    topViolations = counts.head(10)

    fig, ax = plt.subplots()

    # User can choose the color of the bar graph
    color = st.color_picker("Choose Graph Color:", '#9ed6f7')

    ax.bar(topViolations.index, topViolations, color=color)
    ax.set_xlabel('Violation Type', fontweight='bold', fontsize=12)
    ax.set_ylabel('Count', fontweight='bold', fontsize=12)
    ax.set_title('Top 10 Violation Types in Boston', fontweight='bold', fontsize=14)
    ax.set_xticks(range(len(topViolations.index)))
    ax.set_xticklabels(topViolations.index, rotation=30, ha='right', fontsize=10)
    fig.set_facecolor('#dbedff')

    st.pyplot(fig)

    st.divider()

    st.header("Top Violation Types by City")
    # Filter DataFrame based on selected city
    city = st.selectbox("Select City", sorted(df['City'].dropna().unique()))
    filtered_df = df[df['City'] == city]

    # Grouping by violation type and status
    type_status_df = filtered_df.groupby(['Violation Type', 'Status']).size().unstack(fill_value=0)

    # Check if 'Open' and 'Closed' columns exist (I had a problem with one city only having 1 violation)
    if 'Open' not in type_status_df.columns or 'Closed' not in type_status_df.columns:
        st.warning(f"No open or closed violations found in {city}.")
    else:
        # Sum the counts for each violation type
        type_status_df['Total'] = type_status_df['Closed'] + type_status_df['Open']

        # Sort by the total count and select the top 20 violations
        type_status_df = type_status_df.sort_values(by='Total', ascending=False).head(20)

        # Plotting the data
        fig, ax = plt.subplots(figsize=(10, 6))

        # Bar chart for closed violations
        ax.bar(type_status_df.index, type_status_df['Closed'], label='Closed', alpha=0.7, color='#fa6868')

        # Bar chart for open violations (on top)
        ax.bar(type_status_df.index, type_status_df['Open'], bottom=type_status_df['Closed'], label='Open', alpha=0.7,
               color='#6cef6d')

        ax.set_xlabel('Violation Type', fontsize=14, fontweight='bold')
        ax.set_ylabel('Violation Count', fontsize=14, fontweight='bold')
        ax.set_title(f'Top 20 Violations Types in {city}', fontsize=18, fontweight='bold')
        ax.legend()
        plt.xticks(rotation=45, ha='right')

        # Showing the chart using st.pyplot()
        fig.set_facecolor('#dbedff')
        st.pyplot(fig)

        # Using function to display statistics related to bar chart
        totalViolations, openViolations, closedViolations, most_frequent_violation, most_frequent_count = calculate_city_statistics(
            df, city)

        st.info(f"Total Violations in {city}: {totalViolations}")
        st.info(f"Open Violations in {city}: {openViolations}")
        st.info(f"Closed Violations in {city}: {closedViolations}")
        st.info(f"Most Frequent Violation Type in {city}: {most_frequent_violation}, Count: {most_frequent_count}")


def page3(df):
    st.header("Ward Violation Analysis")

    # Sorting the wards in ascending order
    wards = sorted(df['Ward'].unique())

    # User selects a ward
    ward = st.selectbox("Select Ward", wards)

    # Filter the df based on the selected ward
    df_filtered = df[df['Ward'] == ward]

    # Display information about the selected ward
    st.write("Selected Ward:", ward)

    # Display the cities in the selected ward
    cities_in_ward = df_filtered['City'].unique()
    st.write("Cities in the Ward:", ', '.join(cities_in_ward))

    if not df_filtered.empty:
        # bBar chart or pie chart showing the percentage of open vs. closed violations
        violationCounts = df_filtered['Status'].value_counts()
        labels = violationCounts.index
        values = violationCounts.values

        # Plotting the data
        fig, ax = plt.subplots()
        if st.checkbox("Show as Pie Chart"):
            ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90, colors=['#fa6868', '#6cef6d'])
            ax.axis('equal')
        else:
            ax.bar(labels, values, color=['#fa6868', '#6cef6d'])

        ax.set_title("Violation Status Distribution", fontsize=16, fontweight='bold')
        ax.set_xlabel("Violation Status", fontsize=14)
        ax.set_ylabel("Count", fontsize=14)
        fig.set_facecolor('#dbedff')

        st.pyplot(fig)

        # Divide the charts from the additional information
        st.divider()

        # Code for an arrow icon!
        arrow = "&#8594;"

        # Display additional information based on the selected ward
        # Used markdown to make sure I wasn't using the h3 css I had applied originally in the final.css file
        st.markdown("<h3 style='text-align: left;'>Additional Information:</h3>", unsafe_allow_html=True)
        st.write(f"Total Violation Count in Ward {ward} {arrow} {len(df_filtered)}")

        most_frequent_violation = df_filtered['Violation Type'].mode().values[0]
        most_frequent_count = df_filtered['Violation Type'].value_counts().max()

        st.write(f"Most Frequent Violation Type:")
        st.write(f"{most_frequent_violation} {arrow} {most_frequent_count}")

        least_frequent_violation = df_filtered['Violation Type'].value_counts().idxmin()
        least_frequent_count = df_filtered['Violation Type'].value_counts().min()
        st.write(f"Least Frequent Violation Type:")
        st.write(f"{least_frequent_violation} {arrow} {least_frequent_count}")

    else:
        st.warning("No data available. Select another ward!")


def page4(df):
    st.header("Compare Cities")

    # Multi-select for cities
    selected_cities = st.multiselect("Select Cities", sorted(df['City'].unique()))

    # Check if at least two cities are selected
    if len(selected_cities) < 2:
        st.warning("Please select at least two cities.")
        # Display an image when no cities are selected
        st.image("stats.png", width=150)
        return

    # Filter DataFrame based on selected cities
    df_filtered = df[df['City'].isin(selected_cities)]

    # Calculate and display metrics for each city
    cityInfo = []
    for city in selected_cities:
        city_data = df_filtered[df_filtered['City'] == city]
        total_violations = len(city_data)
        open_violations = len(city_data[city_data['Status'] == 'Open'])
        closed_violations = len(city_data[city_data['Status'] == 'Closed'])

        # Calculate percentages
        percentOpen = (open_violations / total_violations) * 100
        percentClosed = (closed_violations / total_violations) * 100

        # Find the most common violation type and its count
        most_common_type = city_data['Violation Type'].mode().values[0]
        count = city_data[city_data['Violation Type'] == most_common_type].count()[
            'Violation Type']

        cityInfo.append({
            'City': city,
            'Total Violations': total_violations,
            'Percentage Open Violations': f"{percentOpen:.0f}%",
            'Percentage Closed Violations': f"{percentClosed:.0f}%",
            'Most Common Violation Type': f"{most_common_type}: {count}"
        })

    # Create a DataFrame from the metrics with 'City' as the index
    cityInfo_df = pd.DataFrame(cityInfo)
    cityInfo_df.set_index('City', inplace=True)

    # Display the table with metrics
    st.write("Metrics for Each City:")
    st.table(cityInfo_df)


def main():
    df = loadData()

    # I used a css file to style my streamlit page
    # I inspected the webpage to pull the exact class names to alter (see final.css)
    # I watched this youtube video to learn how to do this: (https://www.youtube.com/watch?time_continue=291&v=gr_KyGfO_eU&embeds_referring_euri=https%3A%2F%2Fwww.bing.com%2F&embeds_referring_origin=https%3A%2F%2Fwww.bing.com&source_ve_path=MzY4NDIsMjg2NjY&feature=emb_logo)
    with open('final.css') as file:
        css_code = file.read()
        st.markdown(f'<style>{css_code}</style>', unsafe_allow_html=True)

        # I used streamlit-option-menu to get a navigation bar at the top of my webpage
        # See here (https://discuss.streamlit.io/t/streamlit-option-menu-is-a-simple-streamlit-component-that-allows-users-to-select-a-single-item-from-a-list-of-options-in-a-menu/20514)
        menu_selection = option_menu(None, ['Home Page', "Violation Map", "Top Violations", "Ward Analysis", "City Comparison"],
                                     orientation='horizontal',
                                     icons=['house', 'house', 'house', 'house', 'house', 'house', 'house'],
                                     default_index=0,
                                     styles={
                                               "options": {"text-align": "center", "font-size": "15px", "font-weight": 100},
                                               "container": {"padding": "5px", "background-color": "#fafafa"},
                                               "icon": {"color": '#00479a', "font-size": "15px", "text-align": "center"},
                                               "nav-link": {"font-size": "18px", "text-align": "center", "margin": "0px",
                                                            "--hover-color": '#d6e9ff'},
                                               "nav-link-selected": {"background-color": '#2b8dff'},
                                                })

        if menu_selection == "Home Page":
            homePage()
        if menu_selection == "Violation Map":
            page1(df)
        if menu_selection == "Top Violations":
            page2(df)
        if menu_selection == "Ward Analysis":
            page3(df)
        if menu_selection == "City Comparison":
            page4(df)


if __name__ == "__main__":
    main()
