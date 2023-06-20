
🪄 Installation
++++++++++++++++

Clone Deeper Repo
-----------------

To clone the deeper repository, use the following command:

.. code-block:: shell

   git clone https://github.com/the-deep/deeper.git deep-project-root

Go to Deeper Project Root
-------------------------

Navigate to the deeper project root directory:

.. code-block:: shell

   cd deep-project-root

Clone Client, Server, and Other Repos
--------------------------------------

To clone the server repository, use the following command:

.. code-block:: shell

   git clone https://github.com/the-deep/server.git server

To clone the client repository, use the following command:

.. code-block:: shell

   git clone https://github.com/the-deep/client.git client

To clone the client repository (ARY branch), use the following command:

.. code-block:: shell

   git clone --branch=feature/only-ary https://github.com/the-deep/client.git ./ary-only-client

To clone the Deepl services repository, use the following command:

.. code-block:: shell

   git clone https://github.com/the-deep/deepl-deep-integration.git deepl-service

Modify Deepl Service Dockerfile (for M1 Mac)
--------------------------------------------

If you are using a Mac with an M1 chip, make the following modification to the `deepl-service/Dockerfile` file:

Change the `FROM` statement to specify the `amd64` platform:

.. code-block:: Dockerfile

   FROM --platform=linux/amd64 python:3.10-slim-buster

Disable Airplay Receiver (for Mac)
----------------------------------

If you are on a Mac, disable the 'Airplay Receiver' from 'System Preferences > Sharing' to make port 5000 available for use.

Start Servers with Docker Compose
---------------------------------

To start the servers using Docker Compose, follow these steps:

1. Make sure you have the latest versions of Docker and Docker Compose installed.

2. Build the Docker containers:

.. code-block:: shell

   docker-compose build

3. Start the servers:

.. code-block:: shell

   docker-compose up

Useful Commands
----------------

- To migrate, go to the docker container and run migrate command:

.. code-block:: shell

   docker-compose exec web ./manage.py migrate

- To test, go to the docker container and run the test command:

.. code-block:: shell

   docker-compose exec web ./manage.py test

- To add a new package the following steps

1. In the server directory

.. code-block:: shell

   Add package in pyproject.yml file

   Run `poetry lock --no-update`.This will update poetry.lock

2. In the deeper directory

.. code-block:: shell
   
   docker compose up --build
   