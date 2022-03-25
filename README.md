# spotify-skipper
##### A python program to automatically skip unwanted songs.

## Installation

### Python Package

Works on Windows and Linux, but song score is unavailable on Windows.

You can install the [pypi](https://pypi.org/project/autoskip/) package using `pip3 install autoskip`. 

Make sure wherever it is installed to is on your path. You can check with `pip3 show autoskip`.

## Usage

```bash
autoskip # Normal usage
autoskip -h # See help
```
Using any flags will not start the CLI, to make scripting easier. Use --run to prevent this.

|  Short |  Long             | Description                                                 | 
|--------|-------------------|-------------------------------------------------------------|
| -h     | --help            | Shows CLI help and exits                                    |
| -s     | --skip            | Skips current track                                         |
| -wls   | --whitelist-song  | Toggle whitelist for current song                           |
| -wla   | --whitelist-artist| Toggle whitelist for current artist                         |
| -bls   | --blacklist-song  | Toggle blacklist for current song                           |
| -bla   | --blacklist-artist| Toggle blacklist for current artist                         |
| -n     | --notify          | Toggle notifications                                        |
| -r     | --run             | Run the CLI regardless of flags                             |

