import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
import pandas_gbq as pgbq
from google.oauth2 import service_account
from google.cloud import bigquery
import base64

# st.write(st.secrets) 

try:
    # Initialize BigQuery client
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp"]
    )
    client = bigquery.Client(
        project=credentials.project_id,
        credentials=credentials
    )

    custom_css = """
    <style>
    p {
        line-height: 1.75; /* Adjust this value to control the spacing */
        margin-bottom: 0.5rem; /* Optional: Reduce bottom margin for tighter spacing */
    }

    ul {
        margin-top: 0.1rem; /* Adjust this value to control spacing above bullets */
        margin-bottom: 0.8rem; /* Adjust this value to control spacing below bullets */
    }

    li {
        margin-bottom: 0.2rem; /* Adjust this value to control spacing between bullets */
    }

    details {
        margin-bottom: 20px; /* Adjust this value as needed */
    }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

    project_id = 'aljohnsonex'
    dataset_id = 'TRUMP'
    region = 'us'


    # calendar processing
    calendar_sql = """
    SELECT * FROM `aljohnsonex.TRUMP.calendar`
    """

    calendar = pgbq.read_gbq(calendar_sql, project_id=project_id, dialect='standard', credentials=credentials)  # Use credentials here!

    summary_sql = """
    SELECT *
    FROM `aljohnsonex.TRUMP.consolidated`
    """

    summary = pgbq.read_gbq(summary_sql, project_id=project_id, dialect='standard', credentials=credentials) # Use credentials here!

    summary = summary.sort_values(by='date', ascending=False)

    weekly = pgbq.read_gbq("""SELECT * FROM `aljohnsonex.TRUMP.weekly`""", project_id=project_id, dialect='standard', credentials=credentials) # Use credentials here!

    most_recent_weeks = weekly['week'].drop_duplicates()
    weekly = weekly[weekly['week'].isin(most_recent_weeks)]

    def format_date(date):
        day = date.day
        suffix = 'st' if day == 1 else 'nd' if day == 2 else 'rd' if day == 3 else 'th'
        return date.strftime('%A, %B ') + str(day) + suffix

    calendar['formatted_date'] = calendar['date'].apply(format_date)

    calendar['time'] = pd.to_datetime(
        calendar['time'], 
        format='%H:%M:%S', 
        errors='coerce'
    ).dt.time

    calendar['time'] = calendar['time'].fillna(pd.to_datetime('00:01:00').time())
    calendar['time_formatted'] = calendar['time'].apply(
        lambda x: x.strftime('%I:%M %p') if x != pd.to_datetime('00:01:00').time() else ''
    )

    # Get 3 most recent unique dates
    most_recent_dates = calendar['date'].drop_duplicates().nlargest(7)

    # Filter and sort calendar_today
    calendar_today = calendar[calendar['date'].isin(most_recent_dates)]
    calendar_today = calendar_today.sort_values(
        by=['date', 'time'], 
        ascending=[False, True]  # Recent dates first, times ascending within dates
    )


    def format_calendar_with_expanders(df):
        unique_dates = df['formatted_date'].unique()
        for index, date in enumerate(unique_dates):
            with st.expander(date, expanded=(index == 0)):  # Open first expander by default
                group = df[df['formatted_date'] == date]
                group = group.sort_values('time', ascending=True)
    
                for _, row in group.iterrows():
                    time_part = f"{row['time_formatted']}: " if row['time_formatted'] else ""
                    st.markdown(f"<p>{time_part}{row['details']}</p>", unsafe_allow_html=True)
    
                    if pd.notna(row['url']):
                        st.markdown(f"<a href='{row['url']}' target='_blank'>Transcript</a>", unsafe_allow_html=True)
                    if pd.notna(row['video_url']):
                        st.markdown(f"<a href='{row['video_url']}' target='_blank'>Video</a>", unsafe_allow_html=True)

    image = Image.open('./capitol.png')

    with open('./capitol.png', "rb") as img_file:
        encoded_image = base64.b64encode(img_file.read()).decode()
    
    # Center the image using HTML and CSS
    st.markdown(
        f"""
        <style>
        .centered-image {{
            display: block;
            margin-left: auto;
            margin-right: auto;
            margin-top: 30px; /* Adjust this value to move the image down */
            width: 75px; /* Set the width of the image */
        }}
        </style>
        <img class="centered-image" src="data:image/png;base64,{encoded_image}" alt="Capitol Image">
        """,
        unsafe_allow_html=True,
    )
    
    
    # Title and subtext styling
    st.markdown(
        """
        <style>
        .custom-subtext {
            text-align: center; /* Center the text */
            font-style: italic; /* Italicize the text */
            font-size: 14px; /* Adjust font size if needed */
            margin-top: -20px; /* Adjust spacing above (decrease margin) */
            margin-bottom: 0px; /* Adjust spacing below (decrease margin) */
        }
        a.custom-link {
            color: #1a73e8; /* Google blue color for links */
            text-decoration: none; /* Remove underline from links */
        }
        a.custom-link:hover {
            text-decoration: underline; /* Add underline on hover */
        }
        hr {
            margin-top: 0px; /* Adjust top margin of divider (decrease) */
            margin-bottom: 0px; /* Adjust bottom margin of divider (decrease) */
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    
    # Title (centered)
    st.markdown("<h2 style='text-align: center; margin-left: 20px'>White House Tracker</h2>", unsafe_allow_html=True)
    
    # Subtext (centered and italicized with scoped styles)
    st.markdown(
        """<p class="custom-subtext">
        All data collected from 
        <a class="custom-link" href="https://www.rollcall.com" target="_blank">Roll Call</a> 
        and 
        <a class="custom-link" href="https://www.whitehouse.gov" target="_blank">White House</a>
        </p>""",
        unsafe_allow_html=True,
    )
    
    st.divider()

    col1, col2 = st.columns([1, 1.5])

    with col1:
        st.markdown("""
        <style>
        h3 {
            margin-top: 1rem !important; /* Adjust this value to move the header down */
            margin-bottom: -1rem !important; /* Optional: Adjust bottom margin */
            margin-left: 20px !important; /* Keep alignment consistent with Recent Events */
        }
        .stMarkdown {
            margin-top: 0;
        }
        .vertical-line {
            border-left: 2px solid #e0e0e0;
            height: 800px;
            position: absolute;
            left: 105%;
            margin-left: -1px;
            top: 5rem;
        }
        </style>
        <h3>Trump Calendar</h3>
        """, unsafe_allow_html=True)

        format_calendar_with_expanders(calendar_today)

    with col2:
        st.markdown("""
        <style>
        h4 {
            margin-left: 20px !important;  # Match left margin with Trump Calendar
            margin-top: -1rem !important;  # Match top margin with Trump Calendar
            margin-bottom: 1rem !important;  # Match bottom margin with Trump Calendar
        }
        .stExpander {
            border: none !important;
            box-shadow: none !important;
            margin-left: 20px;  # Adjust left margin of expanders
        }
        .streamlit-expanderHeader {
            font-size: 1em !important;  # Adjusted from 5em to 1.2em for better sizing
            font-weight: bold !important;
        }
        .custom-expander .streamlit-expanderHeader {
        font-size: 5em !important;
        font-weight: bold !important;
        color: #4A4A4A;  /* Adjust color as needed */
        }
        .date-paragraph {
            margin-left: 0px !important;
            text-align: left;
            margin-bottom: 0.3rem;
        }
        .transcript-paragraph {
            margin-left: 20px !important;
            text-align: left;
            margin-bottom: 0.3rem;
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown("<h4>Recent Events</h4>", unsafe_allow_html=True)
        
        sorted_weeks = weekly.sort_values(by='week', ascending=False)
        
        for i, week_row in enumerate(sorted_weeks.iterrows()):
            week_data = week_row[1]  # Access the Series from the tuple
            week_date = week_data['week']
            
            # Use expanded=True for the first expander
            with st.expander(f"Week of {week_date.strftime('%B %-d, %Y')}", expanded=(i == 0)):
                st.markdown(f"<p><strong>tldr; </strong> {week_data['summary']}</p> ", unsafe_allow_html=True)
                
                st.markdown("<hr>", unsafe_allow_html=True)

                week_events = summary[summary['calendar_week'] == week_date]
                for _, row in week_events.iterrows():
                    title_prefix = f"{row['type']}: " if row['type'] == "Action" else ""
                    formatted_title = row['title'].split(' - ', 1)[0].title()
                    
                    st.markdown(f"<h5>{title_prefix}{formatted_title}</h5>", unsafe_allow_html=True)
                    
                    transcript_link = f'<a href="{row["url"]}">Transcript</a>' if pd.notna(row['url']) else ""
                    video_link = f'<a href="{row["video_url"]}">Video</a>' if pd.notna(row['video_url']) and row['type'] != "Action" else ""
                    links = ', '.join(filter(None, [transcript_link, video_link]))
                    
                    if links:
                        st.markdown(f'<p class="date-paragraph">{row["formatted_date"]} - {links}</p>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<p class="date-paragraph">{row["formatted_date"]}</p>', unsafe_allow_html=True)
                    
                    bullets = row['summary'].split('- ')
                    for bullet in bullets:
                        if bullet.strip():
                            parts = bullet.split(': ', 1)
                            if len(parts) == 2:
                                topic, description = parts
                                st.markdown(f"<p class='transcript-paragraph'><u>{topic.strip()}</u>: {description.strip()}</p>", unsafe_allow_html=True)
                            else:
                                st.markdown(f"<p class='transcript-paragraph'>{bullet.strip()}</p>", unsafe_allow_html=True)
                    
                    st.markdown("<hr>", unsafe_allow_html=True)
except Exception as e:
    st.error(f"An error occurred: {e}")
    st.stop()
