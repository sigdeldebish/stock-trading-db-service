# Stock Trading System - Group 28 

### Mongo DB attached to a web service for CRUD operations for the Stock Trading Database component. 


## Prerequisites
Ensure you have the following installed on your system:
- **Python**: Version 3.8 or higher.
- **Git**: For cloning the repository.
- **Docker Desktop:** For running the service in a local Docker container


## Installation Steps

### 1. Install Python
1. Download Python from the [official website](https://www.python.org/downloads/).
2. Run the installer and ensure the following:
   - Check the box **Add Python to PATH** during installation.
   - Select "Install Now" to proceed with default settings.

### 2. Clone the Repository
1. Open a terminal and navigate to your desired directory.
2. Clone the repository:
   ```bash
   `git clone https://github.com/sigdeldebish/stock-trading-db-service.git`
   
### Run the service locally in docker

1. Start Docker Engine. 
2. Open the `stock-trading-db-service` that you cloned in the IDE of your choice. I prefer PyCharm or VS Code. 
3. Review all the files. 
4. Open terminal and run command `docker ps` to check if the docker engine/daemon is running. 
5. Go to the `docker-compose.yml` file and in line 28, within `volumes`, change the path to the 
    path you want Mongo to store the data in your PC. Example - Create a directory in
    `/Desktop` and copy the absolute path to docker-compose volumes` - /Users/debish/Desktop/mongoPermData:/data/db`

6. Run service in docker with command`docker-comose up` from the terminal after navigating to `stock-trading-db-service` directory.
