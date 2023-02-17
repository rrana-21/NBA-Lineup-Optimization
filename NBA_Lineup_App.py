# # NBA Team Lineup Optimization

#packages to import
import requests 
import pandas as pd
import html5lib
import streamlit as st

app_title = "Assessing the Value: Is the Salary of an NBA Line-up Justified?"
app_sub_title = 'This web application optimizes an ' \
                'NBA line-up by selecting the top players based ' \
                'on the BPM (box plus-minus) scores relative to their salary to provide you with an optimized line-up.'
st.header(app_title)
st.write(app_sub_title)

st.markdown("***")

#set the season year and stats collection mode to "PerGame" so it can be extracted out of the URL as such
season_id = "2022-23"
per_mode = "PerGame"

#URL
player_info_url = "https://stats.nba.com/stats/leaguedashplayerstats?College=&Conference=&Country=&DateFrom=&DateTo=&Division=&DraftPick=&DraftYear=&GameScope=&GameSegment=&Height=&LastNGames=0&LeagueID=00&Location=&MeasureType=Base&Month=0&OpponentTeamID=0&Outcome=&PORound=0&PaceAdjust=N&PerMode="+per_mode+"&Period=0&PlayerExperience=&PlayerPosition=&PlusMinus=N&Rank=N&Season="+season_id+"&SeasonSegment=&SeasonType=Regular%20Season&ShotClockRange=&StarterBench=&TeamID=0&VsConference=&VsDivision=&Weight="


#headers to extract for the stats
headers  = {
    'Connection': 'keep-alive',
    'Accept': 'application/json, text/plain, */*',
    'x-nba-stats-token': 'true',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
    'x-nba-stats-origin': 'stats',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'cors',
    'Referer': 'https://stats.nba.com/',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9'}

#API call
response = requests.get(url = player_info_url, headers = headers).json()

#grab player information
player_info = response["resultSets"][0]['rowSet']

#stats to collect
collist = response["resultSets"][0]['headers']

#JSON to dataframe 
nba_df = pd.DataFrame(player_info, columns = collist)

#make all column headers lower case 
nba_df.columns = map(str.lower, nba_df.columns)

#get average mins played from all nba players
#subtract by 5 in order to bring in any additional players who might excel in short minutes
avg_mins = (nba_df.loc[:, 'min'].mean()) - 5 

#Filter for players based on team
abb_dict = {'ATL':'atlanta-hawks',
            'BKN':'brooklyn-nets',
            'BOS':'boston-celtics',
            'CHA':'charlotte-hornets',
            'CHI':'chicago-bulls',
            'CLE':'cleveland-cavaliers',
            'DAL':'dallas-mavericks',
            'DEN':'denver-nuggets',
            'DET':'detroit-pistons',
            'GSW':'golden-state-warriors',
            'HOU':'houston-rockets',
            'IND':'indiana-pacers',
            'LAC':'los-angeles-clippers',
            'LAL':'los-angeles-lakers',
            'MEM':'memphis-grizzlies',
            'MIA':'miami-heat',
            'MIL':'milwaukee-bucks',
            'MIN':'minnesota-timberwolves',
            'NOP':'new-orleans-pelicans',
            'NYK':'new-york-knicks',
            'OKC':'oklahoma-city-thunder',
            'ORL':'orlando-magic',
            'PHI':'philadelphia-76ers',
            'PHX':'phoenix-suns',
            'POR':'portland-trail-blazers',
            'SAC':'sacramento-kings',
            'SAS':'san-antonio-spurs',
            'TOR':'toronto-raptors',
            'UTA':'utah-jazz',
            'WAS':'washington-wizards'}

team_options = st.selectbox('''Which team's line up would you like to optimize?''',
    (abb_dict.values()))

team = ''

for k, v in abb_dict.items():
    if team_options == v:
        team += k

team_df = nba_df[nba_df['team_abbreviation'] == team]

if team in abb_dict.keys():
    team_full_name = abb_dict[team]
    abb = team.lower()

#filter team based on avg_mins
team_df = team_df[team_df['min'] >= avg_mins]

#keep on the following attributes:'player_id', 'player_name', 'team_id', 'team_abbreviation', 'pts', 'plus_minus'
clean_team_df = team_df[['player_id', 'player_name', 'team_id', 'team_abbreviation', 'pts', 'plus_minus']]

#rank in descending order of plus minus AND assign the rested index values to "BPM Score"
pm_ranked = clean_team_df.sort_values('plus_minus', ascending=False).reset_index()
pm_ranked['BPM Score'] = pm_ranked.index

#we can drop the original index from the pm_ranked dataframe 
pm_ranked = pm_ranked.drop('index', axis=1)

## Dataframe with Box Plus-Minus (BPM) score is 'pm_ranked'

# ### Import player salary data
#data imported from ESPN: "https://www.espn.com/nba/team/roster/_/name/tor/toronto-raptors"
url = 'https://www.espn.com/nba/team/roster/_/name/'+abb+'/'+team_full_name
salary_list = pd.read_html(url)

#get the dataframe of choice from the 'list' of tables brought in by salary_list
salary_df = salary_list[0]

#remove unecessayr column
salary_df = salary_df.drop(['Unnamed: 0'], axis=1)

#remove numbers behind player names from salary_df, also change "Name" attribute to "player_name" to match pm_ranked
salary_df['Name'] = salary_df['Name'].str.replace('\d+', '')

#remove any missing salaray values and sort in descending salary
salary_df = salary_df[salary_df.Salary != '--']

#clean salary attribute
salary_df['Salary'] = salary_df['Salary'].str.replace(',', '')
salary_df['Salary'] = salary_df['Salary'].str.replace('$', '')

#convert datatypes of attributes in the table 


#Name
salary_df['Name'] = salary_df['Name'].astype(str)
#POS
salary_df['POS'] = salary_df['POS'].astype(str)
#Salary
salary_df['Salary'] = salary_df['Salary'].astype(int)

#change name of "Name" attribute to match pm_ranked "player_name"
salary_df = salary_df.rename(columns={'Name': 'player_name'})

#sort by descending salary and assigned the index value to attribute "Salary Score"
salary_df = salary_df.sort_values('Salary', ascending=False).reset_index(drop=True)
salary_df['Salary Score'] = salary_df.index

### Dataframe with Player Salaries is 'salary_df'

# ## Merge two dataframes together
player_df = pm_ranked.merge(salary_df, on='player_name')

#create a column which subtracts BPM Score by the Salary Score and stores it as an absolute value in "PP Score" (Performance by Pay Score)
#multipying salary score by 5 to standardize scores and provide most accurate results 
player_df['PP Score'] = abs(player_df['BPM Score'] - (player_df['Salary Score']*5))

#sort in descending for PP Score
player_df = player_df.sort_values('PP Score', ascending=True)

# ### Top Guards
#from the player_df chose the top two players who have the lowest PP Score with the POS (position) "PG" or "SG"

guards = ['SG', 'PG']
guard_df = player_df[player_df['POS'].isin(guards)]
top_guards = guard_df.head(2)

# ### Top Frontcourt
#from the player_df chose the top three players who have the lowest PP Score with the POS (position) "SF","PF","C"

FC = ['SF', 'PF', "C"]
FC_df = player_df[player_df['POS'].isin(FC)]
top_FC = FC_df.head(3)

#lineup optimized for performance by pay, players who perform the best according to how they are paid
lineup = pd.concat([top_guards,top_FC])

lineup_for_display = lineup[['POS', 'player_name']]
lineup_for_display.rename(columns={'POS':'Position', 'player_name': 'Player Name'}, inplace=True)



st.markdown("***")

st.write("Here are your starting five:")

hide_table_row_index = """
            <style>
            thead tr th:first-child {display:none}
            tbody th {display:none}
            </style>
            """
# Inject CSS with Markdown
st.markdown(hide_table_row_index, unsafe_allow_html=True)

# Display a static table
st.table(lineup_for_display)





