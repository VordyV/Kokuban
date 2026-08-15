# kokuban
___

**Kokuban** is a project implementing an internal overlay for the game Battlefield 2142. It informs the user about the real reason for a connection loss with the game server, more precisely, it displays a dialog box upon a ban or kick event, indicating why it happened. 

When an admin issues a ban or kick to the user, they will see a dialog box with the reason and other information.

## Screenshots

### A window informing the player about their ban
![ae0.png failed to load](https://raw.githubusercontent.com/VordyV/Kokuban/refs/heads/master/media/ae0.png)

### About their kick
![ae0.png failed to load](https://raw.githubusercontent.com/VordyV/Kokuban/refs/heads/master/media/ae1.png)

### Any other useful information
![ae0.png failed to load](https://raw.githubusercontent.com/VordyV/Kokuban/refs/heads/master/media/ae2.png)

## Install

### For game

1. Download the ZIP archive with the files of the latest version. You can download it in the [Releases](https://github.com/VordyV/Kokuban/releases) section;
2. Extract all files from the downloaded archive into the root folder of the game;
3. In the game shortcut, add these arguments: 
    ```
    +kbsaddr (ip address) +kbsport (port)
    ```
  
    - Right-click on the game shortcut;
    - Click on Properties;
    - In the Target input field, add these arguments at the end.
  
    They are needed to configure the connection to the desired server. By default, it is set for a local server at `127.0.0.1` `8080`.

