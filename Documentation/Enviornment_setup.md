## Env Setup 
Setup Python venv
```bash
python3 -m venv venv
source venv/bin/activate
pip install ragas llama-index llama-index-embeddings-openai llama-index-llms-openai python-dotenv pandas seaborn scipy matplotlib
```
Create a `.env` file in the project root and add your GitHub token:
```
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
```
Verify the setup by running `app.py`
```py
$ source venv/bin/activate
(venv) $ python app.py 
The firewall policies blocking outbound traffic are as follows:

1. Policy: OUTBOUND_BLOCK
   - Source IP: 10.1.1.5
   - Destination IP: 8.8.8.8

2. Policy: OUTBOUND_BLOCK
   - Source IP: 10.1.1.6
   - Destination IP: 1.1.1.1
john.doe is unable to connect to the VPN due to repeated login failures recorded in the logs.
(venv) $ 
```