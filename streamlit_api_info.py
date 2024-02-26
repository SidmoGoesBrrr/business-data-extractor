import gspread
import requests
import pandas as pd
import os
import json
from gspread_dataframe import set_with_dataframe
import random
import time
# Authenticate with Google Sheets
from zocrypt import decrypter,encrypter
import streamlit as st
client = gspread.oauth(
    credentials_filename='credentials.json',
    authorized_user_filename='authorized_user.json'
)
import requests
import pandas as pd
import gspread
import streamlit as st
from client import RestClient

# Fetch Data from DataForSEO
def fetch_data_from_dataforseo(category,limit,filter):
    client = RestClient(st.secrets["dataforseo_login"], st.secrets["dataforseo_password"])

    post_data = dict()
    # simple way to set a task
    post_data[len(post_data)] = dict(
        categories=[
            category
        ],
        filters=[],
        limit=limit
    )
    # POST /v3/business_data/business_listings/search/live
    response = client.post("/v3/business_data/business_listings/search/live", post_data)
    # you can find the full list of the response codes here https://docs.dataforseo.com/v3/appendix/errors
    if response["status_code"] == 20000:
        return response['tasks'][0]['result'][0]['items']
    else:
        print("error. Code: %d Message: %s" % (response["status_code"], response["status_message"]))


# Process Data
def process_data(raw_data, display_params=[]):

    if 'None' in display_params or not display_params or raw_data is None:
        # Assuming raw_data is a list of dictionaries, directly convert it to a DataFrame
        return pd.DataFrame(raw_data)
    
    processed_data = []
    # Iterate through each item in raw_data
    for item in raw_data:
        # Use dictionary comprehension to filter out the necessary keys (data points)
        # Only keep keys that are present in display_params
        filtered_item = {}
        for key, value in item.items():
            if key in display_params:
                # Check if the value is a dictionary and convert it to a string
                if isinstance(value, dict):
                    filtered_item[key] = str(value)
                else:
                    filtered_item[key] = value
        processed_data.append(filtered_item)
    
    return pd.DataFrame(processed_data)
        


# Export to Google Sheets
def export_to_google_sheets(df, sheet_name):
    sheet = client.create(sheet_name)  # Creates a new spreadsheet
    worksheet = sheet.get_worksheet(0)  # Select first worksheet
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())  # Update with dataframe
    return sheet.url

# Export to CSV
def export_to_csv_adjusted(df):
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download data as CSV",
        data=csv,
        file_name='data_export.csv',
        mime='text/csv',
    )


# Streamlit UI
def display():
    st.title('Business Data Processing and Export Tool')
    st.image('https://images.inc.com/uploaded_files/image/1920x1080/getty_494497554_171901.jpg')
    category = st.text_input('Enter category', 'Pizza delivery')
    display_params = st.multiselect('Show necessary data points', ['None', 'title', 'description', 'category', 'address', 'phone', 'url', 'domain', 'logo', 'main_image', 'total_photos', 'snippet', 'latitude', 'longitude', 'is_claimed', 'rating', 'rating_distribution' , 'check_url', 'last_updated_time'])
    limit = st.number_input('Enter limit',min_value=1, max_value=100000, value=10,step=1)
    raw_data=[]
    if 'data_fetched' not in st.session_state:
        st.session_state.data_fetched = False

    if 'data_processed' not in st.session_state:
        st.session_state.data_processed = None

    if st.button('Fetch and Process Data') or st.session_state.data_fetched:
        if not st.session_state['data_fetched']:  # To avoid refetching when not necessary
            raw_data = fetch_data_from_dataforseo(category, limit, [])
            st.session_state['data_processed'] = process_data(raw_data, display_params)
            st.session_state['data_fetched'] = True  # Mark data as fetched
        
        if raw_data:
            st.session_state.data_fetched = True
            st.session_state.data_processed = process_data(raw_data, display_params)
            # Display processed data
            if st.session_state.data_processed is not None:
                st.write(st.session_state.data_processed)

           
                if st.button('Export to Google Sheets'):
                    # Your Google Sheets export logic here
                    link = export_to_google_sheets(st.session_state.data_processed, 'DataForSEO_Export')
                    st.success('Data exported to Google Sheets successfully!')
                    st.markdown(f'You can access the Google Sheets here: [Google Sheet]({link})')

                csv_export_button = st.button('Export to CSV')
                if csv_export_button:
                    # Adjusted Export to CSV functionality here
                    export_to_csv_adjusted(st.session_state.data_processed)
                    # Success message and download button logic here

        else:
            st.error('No data found')
            st.write('Trying with sample data...'
                    'Please note that the sample data is generated randomly and does not represent actual data')
            sample_data = [
            {
              "type": "business_listing",
              "title": "Rudy's Pizza Napoletana - Peter Street",
              "description": "For us it’s all about the pizza. Just like in Naples, our dough is made on site every day, takes 24 hours to double ferment and just 60 seconds to cook. It is soft, light and floppy… so fold for strength or tuck in with a knife and fork. Enjoy.",
              "category": "Neapolitan restaurant",
              "category_ids": [
                "neapolitan_restaurant",
                "italian_restaurant",
                "pizza_restaurant",
                "restaurant"
              ],
              "additional_categories": [
                "Italian restaurant",
                "Pizza restaurant",
                "Restaurant"
              ],
              "cid": "11185039208312255219",
              "feature_id": "0x487bb1c27003cbed:0x9b393de62a44b2f3",
              "address": "Petersfield House, Peter St, Manchester M2 5QJ",
              "address_info": {
                "borough": None,
                "address": "Petersfield House, Peter St",
                "city": "Manchester",
                "zip": "M2 5QJ",
                "region": None,
                "country_code": "GB"
              },
              "place_id": "ChIJ7csDcMKxe0gR87JEKuY9OZs",
              "phone": "+441616608040",
              "url": "http://www.rudyspizza.co.uk/peterstreet",
              "domain": "www.rudyspizza.co.uk",
              "logo": "https://lh6.googleusercontent.com/-LHLR9vtmnJU/AAAAAAAAAAI/AAAAAAAAAAA/fRut8Thd0B8/s44-p-k-no-ns-nd/photo.jpg",
              "main_image": "https://lh5.googleusercontent.com/p/AF1QipPKrTP6MjeAzxWvuTHcg8i-k5oSI6nFBOPia24c=w408-h306-k-no",
              "total_photos": 1290,
              "snippet": "Petersfield House, Peter St, Manchester M2 5QJ",
              "latitude": 53.4781966,
              "longitude": -2.2474716999999997,
              "is_claimed": True,
              "attributes": {
                "available_attributes": {
                  "service_options": [
                    "has_seating_outdoors",
                    "has_delivery",
                    "has_takeout",
                    "serves_dine_in"
                  ],
                  "accessibility": [
                    "has_wheelchair_accessible_entrance",
                    "has_wheelchair_accessible_seating",
                    "has_wheelchair_accessible_restroom"
                  ],
                  "offerings": [
                    "serves_alcohol",
                    "serves_beer",
                    "serves_cocktails",
                    "serves_coffee",
                    "has_free_water_refills",
                    "serves_liquor",
                    "serves_vegan",
                    "serves_vegetarian",
                    "serves_wine"
                  ],
                  "dining_options": [
                    "serves_lunch",
                    "serves_dinner",
                    "serves_dessert",
                    "has_seating"
                  ],
                  "amenities": [
                    "has_bar_onsite",
                    "welcomes_children",
                    "has_high_chairs",
                    "has_restroom"
                  ],
                  "atmosphere": [
                    "feels_casual",
                    "feels_cozy",
                    "is_recently_popular"
                  ],
                  "crowd": [
                    "welcomes_families",
                    "suitable_for_groups",
                    "welcomes_lgbtq",
                    "is_transgender_safespace"
                  ],
                  "planning": [
                    "accepts_reservations"
                  ],
                  "payments": [
                    "pay_debit_card",
                    "pay_mobile_nfc"
                  ]
                },
                "unavailable_attributes": {
                  "accessibility": [
                    "has_wheelchair_accessible_parking"
                  ]
                }
              },
              "place_topics": {
                "dough": 41,
                "buffalo mozzarella": 17,
                "queue": 15,
                "topping": 15,
                "white pizza": 11,
                "wood fired": 8,
                "stone baked": 7,
                "incredible pizza": 5,
                "vegan cheese": 5,
                "wild boar": 5
              },
              "rating": {
                "rating_type": "Max5",
                "value": 4.7,
                "votes_count": 2902,
                "rating_max": None
              },
              "rating_distribution": {
                "1": 45,
                "2": 45,
                "3": 90,
                "4": 444,
                "5": 2278
              },
              "people_also_search": [
                {
                  "cid": "3433913040112965233",
                  "feature_id": "0x0:0x2fa7b5b76183d671",
                  "title": "Noi Quattro - Pizzeria",
                  "rating": {
                    "rating_type": "Max5",
                    "value": 4.6,
                    "votes_count": 1064,
                    "rating_max": None
                  }
                },
                {
                  "cid": "1416331994015789952",
                  "feature_id": "0x0:0x13a7d271cb54f380",
                  "title": "Crazy Pedro's Bridge Street",
                  "rating": {
                    "rating_type": "Max5",
                    "value": 4.3,
                    "votes_count": 1690,
                    "rating_max": None
                  }
                },
                {
                  "cid": "782585807451016673",
                  "feature_id": "0x0:0xadc4da543614de1",
                  "title": "Don Marco",
                  "rating": {
                    "rating_type": "Max5",
                    "value": 4.4,
                    "votes_count": 1042,
                    "rating_max": None
                  }
                },
                {
                  "cid": "13945137393035157451",
                  "feature_id": "0x0:0xc18714930fe09fcb",
                  "title": "PLY",
                  "rating": {
                    "rating_type": "Max5",
                    "value": 4.1,
                    "votes_count": 1301,
                    "rating_max": None
                  }
                },
                {
                  "cid": "213701385891634133",
                  "feature_id": "0x0:0x2f738473a145bd5",
                  "title": "Franco Manca Manchester - Piccadilly Gardens",
                  "rating": {
                    "rating_type": "Max5",
                    "value": 4.3,
                    "votes_count": 856,
                    "rating_max": None
                  }
                }
              ],
              "work_time": {
                "work_hours": {
                  "timetable": {
                    "sunday": [
                      {
                        "open": {
                          "hour": 12,
                          "minute": 0
                        },
                        "close": {
                          "hour": 21,
                          "minute": 0
                        }
                      }
                    ],
                    "monday": [
                      {
                        "open": {
                          "hour": 12,
                          "minute": 0
                        },
                        "close": {
                          "hour": 22,
                          "minute": 0
                        }
                      }
                    ],
                    "tuesday": [
                      {
                        "open": {
                          "hour": 12,
                          "minute": 0
                        },
                        "close": {
                          "hour": 22,
                          "minute": 0
                        }
                      }
                    ],
                    "wednesday": [
                      {
                        "open": {
                          "hour": 12,
                          "minute": 0
                        },
                        "close": {
                          "hour": 22,
                          "minute": 0
                        }
                      }
                    ],
                    "thursday": [
                      {
                        "open": {
                          "hour": 12,
                          "minute": 0
                        },
                        "close": {
                          "hour": 22,
                          "minute": 0
                        }
                      }
                    ],
                    "friday": [
                      {
                        "open": {
                          "hour": 12,
                          "minute": 0
                        },
                        "close": {
                          "hour": 22,
                          "minute": 0
                        }
                      }
                    ],
                    "saturday": [
                      {
                        "open": {
                          "hour": 12,
                          "minute": 0
                        },
                        "close": {
                          "hour": 22,
                          "minute": 0
                        }
                      }
                    ]
                  },
                  "current_status": "open"
                }
              },
              "popular_times": {
                "popular_times_by_days": {
                  "sunday": [
                    {
                      "time": {
                        "hour": 6,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 7,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 8,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 9,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 10,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 11,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 12,
                        "minute": 0
                      },
                      "popular_index": 30
                    },
                    {
                      "time": {
                        "hour": 13,
                        "minute": 0
                      },
                      "popular_index": 52
                    },
                    {
                      "time": {
                        "hour": 14,
                        "minute": 0
                      },
                      "popular_index": 66
                    },
                    {
                      "time": {
                        "hour": 15,
                        "minute": 0
                      },
                      "popular_index": 64
                    },
                    {
                      "time": {
                        "hour": 16,
                        "minute": 0
                      },
                      "popular_index": 57
                    },
                    {
                      "time": {
                        "hour": 17,
                        "minute": 0
                      },
                      "popular_index": 60
                    },
                    {
                      "time": {
                        "hour": 18,
                        "minute": 0
                      },
                      "popular_index": 69
                    },
                    {
                      "time": {
                        "hour": 19,
                        "minute": 0
                      },
                      "popular_index": 68
                    },
                    {
                      "time": {
                        "hour": 20,
                        "minute": 0
                      },
                      "popular_index": 51
                    },
                    {
                      "time": {
                        "hour": 21,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 22,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 23,
                        "minute": 0
                      },
                      "popular_index": 0
                    }
                  ],
                  "monday": [
                    {
                      "time": {
                        "hour": 6,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 7,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 8,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 9,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 10,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 11,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 12,
                        "minute": 0
                      },
                      "popular_index": 28
                    },
                    {
                      "time": {
                        "hour": 13,
                        "minute": 0
                      },
                      "popular_index": 36
                    },
                    {
                      "time": {
                        "hour": 14,
                        "minute": 0
                      },
                      "popular_index": 41
                    },
                    {
                      "time": {
                        "hour": 15,
                        "minute": 0
                      },
                      "popular_index": 42
                    },
                    {
                      "time": {
                        "hour": 16,
                        "minute": 0
                      },
                      "popular_index": 44
                    },
                    {
                      "time": {
                        "hour": 17,
                        "minute": 0
                      },
                      "popular_index": 49
                    },
                    {
                      "time": {
                        "hour": 18,
                        "minute": 0
                      },
                      "popular_index": 58
                    },
                    {
                      "time": {
                        "hour": 19,
                        "minute": 0
                      },
                      "popular_index": 64
                    },
                    {
                      "time": {
                        "hour": 20,
                        "minute": 0
                      },
                      "popular_index": 60
                    },
                    {
                      "time": {
                        "hour": 21,
                        "minute": 0
                      },
                      "popular_index": 44
                    },
                    {
                      "time": {
                        "hour": 22,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 23,
                        "minute": 0
                      },
                      "popular_index": 0
                    }
                  ],
                  "tuesday": [
                    {
                      "time": {
                        "hour": 6,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 7,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 8,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 9,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 10,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 11,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 12,
                        "minute": 0
                      },
                      "popular_index": 39
                    },
                    {
                      "time": {
                        "hour": 13,
                        "minute": 0
                      },
                      "popular_index": 45
                    },
                    {
                      "time": {
                        "hour": 14,
                        "minute": 0
                      },
                      "popular_index": 46
                    },
                    {
                      "time": {
                        "hour": 15,
                        "minute": 0
                      },
                      "popular_index": 44
                    },
                    {
                      "time": {
                        "hour": 16,
                        "minute": 0
                      },
                      "popular_index": 46
                    },
                    {
                      "time": {
                        "hour": 17,
                        "minute": 0
                      },
                      "popular_index": 55
                    },
                    {
                      "time": {
                        "hour": 18,
                        "minute": 0
                      },
                      "popular_index": 67
                    },
                    {
                      "time": {
                        "hour": 19,
                        "minute": 0
                      },
                      "popular_index": 75
                    },
                    {
                      "time": {
                        "hour": 20,
                        "minute": 0
                      },
                      "popular_index": 69
                    },
                    {
                      "time": {
                        "hour": 21,
                        "minute": 0
                      },
                      "popular_index": 52
                    },
                    {
                      "time": {
                        "hour": 22,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 23,
                        "minute": 0
                      },
                      "popular_index": 0
                    }
                  ],
                  "wednesday": [
                    {
                      "time": {
                        "hour": 6,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 7,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 8,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 9,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 10,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 11,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 12,
                        "minute": 0
                      },
                      "popular_index": 38
                    },
                    {
                      "time": {
                        "hour": 13,
                        "minute": 0
                      },
                      "popular_index": 44
                    },
                    {
                      "time": {
                        "hour": 14,
                        "minute": 0
                      },
                      "popular_index": 43
                    },
                    {
                      "time": {
                        "hour": 15,
                        "minute": 0
                      },
                      "popular_index": 41
                    },
                    {
                      "time": {
                        "hour": 16,
                        "minute": 0
                      },
                      "popular_index": 45
                    },
                    {
                      "time": {
                        "hour": 17,
                        "minute": 0
                      },
                      "popular_index": 58
                    },
                    {
                      "time": {
                        "hour": 18,
                        "minute": 0
                      },
                      "popular_index": 73
                    },
                    {
                      "time": {
                        "hour": 19,
                        "minute": 0
                      },
                      "popular_index": 79
                    },
                    {
                      "time": {
                        "hour": 20,
                        "minute": 0
                      },
                      "popular_index": 69
                    },
                    {
                      "time": {
                        "hour": 21,
                        "minute": 0
                      },
                      "popular_index": 47
                    },
                    {
                      "time": {
                        "hour": 22,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 23,
                        "minute": 0
                      },
                      "popular_index": 0
                    }
                  ],
                  "thursday": [
                    {
                      "time": {
                        "hour": 6,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 7,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 8,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 9,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 10,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 11,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 12,
                        "minute": 0
                      },
                      "popular_index": 46
                    },
                    {
                      "time": {
                        "hour": 13,
                        "minute": 0
                      },
                      "popular_index": 70
                    },
                    {
                      "time": {
                        "hour": 14,
                        "minute": 0
                      },
                      "popular_index": 58
                    },
                    {
                      "time": {
                        "hour": 15,
                        "minute": 0
                      },
                      "popular_index": 43
                    },
                    {
                      "time": {
                        "hour": 16,
                        "minute": 0
                      },
                      "popular_index": 49
                    },
                    {
                      "time": {
                        "hour": 17,
                        "minute": 0
                      },
                      "popular_index": 63
                    },
                    {
                      "time": {
                        "hour": 18,
                        "minute": 0
                      },
                      "popular_index": 71
                    },
                    {
                      "time": {
                        "hour": 19,
                        "minute": 0
                      },
                      "popular_index": 69
                    },
                    {
                      "time": {
                        "hour": 20,
                        "minute": 0
                      },
                      "popular_index": 58
                    },
                    {
                      "time": {
                        "hour": 21,
                        "minute": 0
                      },
                      "popular_index": 41
                    },
                    {
                      "time": {
                        "hour": 22,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 23,
                        "minute": 0
                      },
                      "popular_index": 0
                    }
                  ],
                  "friday": [
                    {
                      "time": {
                        "hour": 6,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 7,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 8,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 9,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 10,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 11,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 12,
                        "minute": 0
                      },
                      "popular_index": 31
                    },
                    {
                      "time": {
                        "hour": 13,
                        "minute": 0
                      },
                      "popular_index": 44
                    },
                    {
                      "time": {
                        "hour": 14,
                        "minute": 0
                      },
                      "popular_index": 55
                    },
                    {
                      "time": {
                        "hour": 15,
                        "minute": 0
                      },
                      "popular_index": 63
                    },
                    {
                      "time": {
                        "hour": 16,
                        "minute": 0
                      },
                      "popular_index": 68
                    },
                    {
                      "time": {
                        "hour": 17,
                        "minute": 0
                      },
                      "popular_index": 77
                    },
                    {
                      "time": {
                        "hour": 18,
                        "minute": 0
                      },
                      "popular_index": 90
                    },
                    {
                      "time": {
                        "hour": 19,
                        "minute": 0
                      },
                      "popular_index": 100
                    },
                    {
                      "time": {
                        "hour": 20,
                        "minute": 0
                      },
                      "popular_index": 95
                    },
                    {
                      "time": {
                        "hour": 21,
                        "minute": 0
                      },
                      "popular_index": 75
                    },
                    {
                      "time": {
                        "hour": 22,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 23,
                        "minute": 0
                      },
                      "popular_index": 0
                    }
                  ],
                  "saturday": [
                    {
                      "time": {
                        "hour": 6,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 7,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 8,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 9,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 10,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 11,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 12,
                        "minute": 0
                      },
                      "popular_index": 41
                    },
                    {
                      "time": {
                        "hour": 13,
                        "minute": 0
                      },
                      "popular_index": 63
                    },
                    {
                      "time": {
                        "hour": 14,
                        "minute": 0
                      },
                      "popular_index": 79
                    },
                    {
                      "time": {
                        "hour": 15,
                        "minute": 0
                      },
                      "popular_index": 85
                    },
                    {
                      "time": {
                        "hour": 16,
                        "minute": 0
                      },
                      "popular_index": 82
                    },
                    {
                      "time": {
                        "hour": 17,
                        "minute": 0
                      },
                      "popular_index": 80
                    },
                    {
                      "time": {
                        "hour": 18,
                        "minute": 0
                      },
                      "popular_index": 83
                    },
                    {
                      "time": {
                        "hour": 19,
                        "minute": 0
                      },
                      "popular_index": 85
                    },
                    {
                      "time": {
                        "hour": 20,
                        "minute": 0
                      },
                      "popular_index": 78
                    },
                    {
                      "time": {
                        "hour": 21,
                        "minute": 0
                      },
                      "popular_index": 61
                    },
                    {
                      "time": {
                        "hour": 22,
                        "minute": 0
                      },
                      "popular_index": 0
                    },
                    {
                      "time": {
                        "hour": 23,
                        "minute": 0
                      },
                      "popular_index": 0
                    }
                  ]
                }
              },
              "local_business_links": [
                {
                  "type": "reservation",
                  "title": "rudyspizza.co.uk",
                  "url": "https://www.rudyspizza.co.uk/peter-st/"
                },
                {
                  "type": "order",
                  "delivery_services": [
                    {
                      "type": "delivery_services_element",
                      "title": "deliveroo.co.uk",
                      "url": "https://deliveroo.co.uk/menu/manchester/manchester-central/rudys-pizza-peter-street?utm_medium=affiliate&utm_source=google_maps_link"
                    }
                  ]
                },
                {
                  "type": "menu",
                  "title": "rudyspizza.co.uk",
                  "url": "http://rudyspizza.co.uk/menus/"
                }
              ],
              "contact_info": [
                {
                  "type": "telephone",
                  "value": "+441616608040",
                  "source": "google_business"
                },
                {
                  "type": "telephone",
                  "value": "01213145880",
                  "source": "backlinks"
                },
                {
                  "type": "telephone",
                  "value": "01519095505",
                  "source": "backlinks"
                },
                {
                  "type": "telephone",
                  "value": "01142992550",
                  "source": "backlinks"
                },
                {
                  "type": "telephone",
                  "value": "01619690196",
                  "source": "backlinks"
                },
                {
                  "type": "telephone",
                  "value": "01519095109",
                  "source": "backlinks"
                },
                {
                  "type": "mail",
                  "value": "liverpoolcastlest@rudyspizza.co.uk",
                  "source": "backlinks"
                },
                {
                  "type": "mail",
                  "value": "peterstreet@rudyspizza.co.uk",
                  "source": "backlinks"
                },
                {
                  "type": "mail",
                  "value": "sheffield@rudyspizza.co.uk",
                  "source": "backlinks"
                },
                {
                  "type": "mail",
                  "value": "leeds@rudyspizza.co.uk",
                  "source": "backlinks"
                },
                {
                  "type": "mail",
                  "value": "sale@rudyspizza.co.uk",
                  "source": "backlinks"
                }
              ],
              "check_url": "https://www.google.co.uk/maps?cid=11185039208312255219&hl=en&gl=GB",
              "last_updated_time": "2023-02-03 13:14:17 +00:00"
            }
          ]
            st.session_state.data_processed = process_data(sample_data, display_params)
            # Display processed data
            if st.session_state.data_processed is not None:
                st.write(st.session_state.data_processed)

        
                if st.button('Export to Google Sheets'):
                    # Your Google Sheets export logic here
                    link = export_to_google_sheets(st.session_state.data_processed, 'DataForSEO_Export')
                    st.success('Data exported to Google Sheets successfully!')
                    st.markdown(f'You can access the Google Sheets here: [Google Sheet]({link})')

                csv_export_button = st.button('Export to CSV')
                if csv_export_button:
                    # Adjusted Export to CSV functionality here
                    export_to_csv_adjusted(st.session_state.data_processed)
                    # Success message and download button logic here
        st.markdown('---')               
        if st.button('Fetch New Data'):
          # Reset the data fetched state to allow re-fetching
          st.session_state['data_fetched'] = False
          st.session_state['data_processed'] = None
          st.rerun()  # Optionally rerun the app to reset the UI
def main():
    decrypted_password = decrypter.decrypt_text(st.secrets['password'], st.secrets['key'])
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False  # Default to not authenticated

    if st.session_state['authenticated']:
        # If already authenticated, directly display the main app
        display()
    else:
        # Prompt for password
        user_password = st.text_input('Enter password', type='password')
        if user_password == decrypted_password:
            st.session_state['authenticated'] = True
            st.rerun()  # Rerun the app to update the display
        else:
            st.session_state['authenticated'] = False
            if user_password:
              st.error('Incorrect password')

if __name__ == "__main__":
   
    main()