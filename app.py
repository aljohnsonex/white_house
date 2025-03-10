import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
import pandas_gbq as pgbq
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.cloud import bigquery

def get_credentials():
    """Create and refresh OAuth credentials"""
    creds = Credentials(
        token=None,  # Will be auto-populated on refresh
        refresh_token=st.secrets["gcp_oauth"]["refresh_token"],
        client_id=st.secrets["gcp_oauth"]["client_id"],
        client_secret=st.secrets["gcp_oauth"]["client_secret"],
        token_uri=st.secrets["gcp_oauth"]["token_uri"],
        scopes=st.secrets["gcp_oauth"]["scopes"].split(",")
    )
    
    if creds.expired:
        creds.refresh(Request())
        
    return creds, st.secrets["gcp_oauth"]["project_id"]

# Initialize BigQuery client
try:
    credentials, project_id = get_credentials()
    client = bigquery.Client(project=project_id, credentials=credentials)
except Exception as e:
    st.error(f"Failed to initialize BigQuery client: {str(e)}")
    st.error(f"Project ID: {project_id}")
    st.error(f"Credentials: {credentials}")
    raise

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

calendar = pgbq.read_gbq(calendar_sql, project_id=project_id, dialect='standard')

summary_sql = """
SELECT * 
FROM `aljohnsonex.TRUMP.consolidated`
"""

summary = pgbq.read_gbq(summary_sql, project_id=project_id, dialect='standard')

summary = summary.sort_values(by='date', ascending=False)

weekly = pgbq.read_gbq("""SELECT * FROM `aljohnsonex.TRUMP.weekly`""", project_id=project_id, dialect='standard')

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


def format_calendar(df):
    css = """
    <style>
    summary {
        list-style: none;
        cursor: pointer;
        display: flex;
        align-items: center;
    }
    summary svg {
        margin-right: 1px;
        transition: transform 0.2s ease-in-out;
        transform: rotate(0deg);
    }
    details:not([open]) > summary svg {
        transform: rotate(-90deg);
    }
    </style>
    """

    formatted_schedule = [css]
    
    # Get unique dates in their original order
    unique_dates = df['formatted_date'].unique()
    
    for date in unique_dates:
        group = df[df['formatted_date'] == date]
        formatted_schedule.append(f"""
<details open>
    <summary>
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="white">
            <path d="M7 10l5 5 5-5z"/>
        </svg>
        <h5 style="margin: 0; display: inline;">{date}</h5>
    </summary>
    <div style="margin-left: 20px;">
""")
        # Sort group by time before processing
        group = group.sort_values('time', ascending=True)
        
        for _, row in group.iterrows():
            time_part = f"{row['time_formatted']}: " if row['time_formatted'] else ""
            formatted_schedule.append(f"{time_part}{row['details']}")
            
            if pd.notna(row['url']):
                formatted_schedule.append(f"  - [Transcript]({row['url']})")
            if pd.notna(row['video_url']):
                formatted_schedule.append(f"  - [Video]({row['video_url']})")
            formatted_schedule.append("\n")
            
        formatted_schedule.append("</div></details>\n")
    
    return "\n".join(formatted_schedule)

image = Image.open('./capitol.png')

header1, header2 = st.columns([1, 3])

with header1: 
    st.image(image, width = 75)

    hide_img_fs = '''
    <style>
    .stImage {
        margin-top: 30px;  /* Adjust this value to move the image down */
        margin-left: 70px;  /* Adjust this value to move the image right */
    }
    button[title="View fullscreen"] {
        visibility: hidden;
    }
    button[title="View fullscreen"]{
        visibility: hidden;}
    </style>
    '''

    st.markdown(hide_img_fs, unsafe_allow_html=True)

with header2:
    st.markdown("""
    <style>
    .stMarkdown {
        margin-bottom: 0.1rem !important; /* Reduce bottom margin */
    }
    h2 {
        margin-bottom: 0rem !important; /* Reduce bottom margin */            
    }
    hr {
        margin-top: 0.3rem !important; /* Reduce top margin of divider */
        margin-bottom: 0.1rem !important; /* Reduce bottom margin of divider */
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""<h2>White House Tracker</h2>""", unsafe_allow_html=True)

    st.markdown("*All data collected from www.rollcall.com and www.whitehouse.gov*")

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
    <div class="vertical-line"></div>
    """, unsafe_allow_html=True)

    st.markdown(format_calendar(calendar_today), unsafe_allow_html=True)

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
 
