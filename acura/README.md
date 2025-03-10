# Acura

Acura(tor) is the curator service. It listens to the RabbitMQ queue "curator" and curates music data when a message is received. The curator service is responsible for curating the music data for the next day.

The curator service is meant to be run as a separate service. It is not meant to be run as a part of the backend service.

Typical workflow:

1. The backend requests the curator to curate the data by sending a RabbitMQ message.
2. The curator receives the message and curates the data.
3. In case nothing has been curated for today (or the next day), the curator will curate the data.
4. The curator sends a RabbitMQ message to the backend to notify the backend that the data has been curated.
5. The playlists are retrieved from the database and streamed back to the client as fast as possible.

## Requirements

- Python 3.10+ (tested version is 3.11.2)
- RabbitMQ
- PostgreSQL

## Environment Variables

OpenAI, and Discogs.com API keys are required for running this software. Additionally, you must have a valid AMQP-compatible server for handling incoming messages. The documentation assumes that you are using RabbitMQ.

- `RMQ_HOST`: The hostname of the RabbitMQ server.
- `RMQ_PORT`: The port of the RabbitMQ server.
- `RMQ_USER`: The username for RabbitMQ authentication.
- `RMQ_PASS`: The password for RabbitMQ authentication.
- `DISCOGS_USER_TOKEN`: The user token for [Discogs API](http://discogs.com/developers).
- `OPENAI_API_KEY`: The [API key for OpenAI](https://platform.openai.com/).

## Running the Service

To run the curator service, use the following commands:

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables or set them in .env file
export RMQ_HOST=your_rabbitmq_host
export RMQ_PORT=your_rabbitmq_port
export RMQ_USER=your_rabbitmq_user
export RMQ_PASS=your_rabbitmq_password
export DISCOGS_USER_TOKEN=your_discogs_user_token
export OPENAI_API_KEY=your_openai_api_key

# Start the service
python .
```

From this point on, the service will run indefinitely and will accept all the incoming messages.
