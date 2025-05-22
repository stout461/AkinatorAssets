testing

Steps I used to Connect to my VM instance. 

Connect to the instance. 

chmod 400 ~/Downloads/AkinatorAuth.pem
ssh -i ~/Downloads/AkinatorAuth.pem ubuntu@Public IP here # Ommiting becuase this is public repo

=======================================

Install Dependencies... 

sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip -y

=======================================

Next need to creat venv

python3 -m venv venv
source venv/bin/activate

=======================================

Now we can install dependencies. 

pip install flask pandas plotly yfinance apscheduler pytz xlsxwriter matplotlib

=======================================

Optional, Set python venv to run whenever SSH is initiated. (Should not need to be done again.)

echo 'source ~/venv/bin/activate' >> ~/.bashrc
source ~/.bashrc

=======================================

Upload the scripts to be ran. 

C:\Users\stout\IdeaProjects\AkinatorAssets\src

scp -i ~/Downloads/AkinatorAuth.pem -r ~/IdeaProjects/AkinatorAssets/src/AkinatorAssets_2030Targets_AutoRefresh.py ~/IdeaProjects/AkinatorAssets/src/run_watchlist_scriptv2.py ~/IdeaProjects/AkinatorAssets/src/templates ~/IdeaProjects/AkinatorAssets/src/static ubuntu@Public IP here # Ommiting becuase this is public repo