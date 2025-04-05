# AI-Powered Candidate Search

An AI-driven application that enables users to search for candidate profiles based on specific requirements. This project leverages Streamlit for the user interface, Google's Generative AI for natural language processing, and supports both MongoDB and SQL databases for data storage and retrieval.

## Features

- **Natural Language Querying**: Users can input search queries in plain English, which are then processed by Google's Generative AI to generate corresponding database queries.
- **Dual Database Support**: The application can interact with both MongoDB and SQL databases, allowing flexibility in data storage solutions.
- **Streamlit Interface**: Provides an intuitive and interactive web interface for users to input queries and view results.
- **Real-time Results**: View candidate profiles that match your criteria instantly.

## Installation

### Prerequisites

- Python 3.8+
- MongoDB (if using MongoDB as your database)
- SQL Database (if using SQL as your database)
- Google API Key for Generative AI


### Steps

1. **Clone the Repository**:

```shellscript
git clone https://github.com/Prathamesh72003/SmartSearchLLm.git
cd SmartSearchLLm
```


2. **Install Required Packages**:

```shellscript
pip install -r requirements.txt
```


3. **Set Up Environment Variables**:
Create a `.env` file in the project root and add the following:

```ini
GOOGLE_API_KEY=your_google_api_key
MONGO_CONNECTION_STRING=your_mongo_connection_string
```


## Usage

1. **Run the Application**:

```shellscript
streamlit run mongodb.py
streamlit run sql.py
```


2. **Access the Interface**:
Open your web browser and navigate to [http://localhost:8501](http://localhost:8501) to use the application.
3. **Enter Your Query**:
Type a natural language query like "Find candidates with 5+ years of Python experience who know React and have worked in fintech."
4. **View Results**:
The application will display matching candidate profiles based on your query.


## File Structure

```plaintext
SmartSearchLLm/
├── mongodb.py              # MongoDB query execution and validation
├── sql.py                  # SQL database query execution and validation
├── requirements.txt        # Python dependencies
├── .env                    # Example environment variables file
├── .gitignore              # Project documentation
```

## How It Works

The application follows this workflow:

1. User enters a natural language query
2. Google Generative AI processes the query
3. The system generates appropriate database queries
4. Queries are executed against MongoDB or SQL database
5. Results are processed and formatted
6. Matching candidate profiles are displayed to the user


## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a new branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Commit your changes (`git commit -m 'Add some amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request


## Acknowledgments

- Google Generative AI for powering the natural language processing 
- Streamlit for the interactive web interface
- MongoDB and SQL database communities
