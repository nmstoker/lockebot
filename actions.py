import os
import sys
import configparser
import random
from typing import Text, Dict, Any, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

import arrow
from num2words import num2words
from text2digits import text2digits
import roman
import sqlite3

ruler_gender_pronouns = {'queen':{'HeShe':'She'}, 'king':{'HeShe':'He'}}

def match_template(intent, fields):
    templates = {
        'ruler_list':{'fields': '$Name $Number'},
        'ruler_before':{'fields': '$Name $Number'},
        'ruler_after':{'fields': '$Name $Number'},
    }


def nthwords2int(nthword):
    """Takes an "nth-word" (eg 3rd, 21st, 28th) strips off the ordinal ending
    and returns the pure number."""

    ordinal_ending_chars = 'stndrh'  # from 'st', 'nd', 'rd', 'th'

    try:
        int_output = int(nthword.strip(ordinal_ending_chars))
    except Exception as e:
        raise Exception('Illegal nth-word: ' + nthword)

    return int_output


def map_entity_to_number(ent):
    """Takes a complete entity and returns the corresponding number (as a
    string)"""

    # self.logger.debug(
    #     'Entity: value: ' + ent['value'] + ' of type: ' + ent['entity'])
    etype = ent['entity']

    if etype == 'number':
        # TODO: Add error and type checking
        return ent['value']
    if etype == 'number-roman':
        # TODO: Add better error and type checking
        try:
            return str(roman.fromRoman(ent['value'].upper()))
        except:
            return None
    if etype == 'nth':
        # TODO: Add better error and type checking
        try:
            print('converting using nthwords2int')
            return str(nthwords2int(ent['value'].lower()))
        except:
            return None
    if etype in ('nth-words', 'number-words', 'year-words'):
        # TODO: Add better error and type checking
        try:
            t2d = text2digits.Text2Digits()
            return str(t2d.convert(ent['value'].lower()))
        except:
            return None

    # so we couldn't match the etype to convert
    return None


def map_feature_to_field(feature):
    """Takes a feature string and returns a list of the corresponding
    database fieldname(s) (usually just one but can handle more)"""

    #self.logger.debug('Feature to map: ' + feature)

    f = feature.lower()

    # NB: this structure assumes all features will be mapped by at least one of
    # the conditions below; if you have acceptable features that should be
    # passed through then some slight changes to the logic would be needed.

    if f in ('events', 'happening', 'happenings'):
        return ['NotableEventsDuringLife']
    if f in ('describe', 'description', 'brief description', 'about'):
        return ['Description']
    if f in ('born', 'birth'):
        return ['DtBirth']
    if f in ('die', 'died', 'death'):
        return ['DtDeath']
    if f in ('king from','queen from', 'reign from', 'reign begin', 'reign began', 'reign start', 'started', 'become', 'rule from', 'rule start', 'rule began', 'on the throne', 'on throne'):
        return ['ReignStartDt']
    if f in ('king until','queen until', 'reign until', 'reign to', 'reign end', 'reign ended', 'end', 'become', 'rule until'):
        return ['ReignEndDt']
    if f in ('cause of death', 'killed', 'circumstances'):
        return ['DeathCircumstances']
    if f == 'house':
        return ['House']
    if f in ('portrait', 'picture', 'look', 'painting'):
        return ['Portrait']
    if f == 'title':
        return ['Title']
    if f in ('country', 'where'):
        return ['Country']
    if f in ('battle', 'battles', 'famous battles', 'wars', 'war', 'fight', 'fought'):
        return ['FamousBattles']
    if f in ('person', 'individual'):
        return ['Name']
    if f == 'number':
        return ['Number']
    if f in ('all', 'about'):
        return ['Name', 'Number', 'DtBirth', 'DtDeath', 'ReignStartDt', 'ReignEndDt', 'FamousBattles', 'Description']
    # so we didn't match anything
    return []


def format_row(row, spoken=True):
    for item in row:
        if 'Dt' in str(item):
            if (row[item] is not None) & (row[item] != '') & (row[item] != 'Present'):
                try:
                    if spoken:
                        row[item] = str('the ' + num2words(int(arrow.get(str(row[item]), 'YYYY-MM-DD').format('D')), to='ordinal') + ' of ' + str(arrow.get(str(row[item]), 'YYYY-MM-DD').format('MMMM YYYY')))
                    else:
                        row[item] = str(arrow.get(str(row[item]), 'YYYY-MM-DD').format('D MMMM YYYY'))
                except Exception as e:
                    print('Cannot convert contents of date field ' + str(item) + ' to a formatted date. ' + str(e))
        if item in ('Number'):
            if spoken:
                row[item] = str('the ' + num2words(int(row[item]), to='ordinal'))
            else:
                row[item] = str(roman.toRoman(int(row[item])))
    return row

def merge_output(row):
    output = ''
    for f in row:
        try:
            output = output + str(row[f]) + ', '
        except UnicodeEncodeError:
            output = output + str(row[f].encode('utf-8')) + ', '
    # TODO: put something to take off the final comma
    return output


def dict_factory(cursor, row):
    """Used for handling sqlite rows as dictionary (source: http://stackoverflow.com/questions/3300464/how-can-i-get-dict-from-sqlite-query)"""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

#TODO think about where this sits best...
config = configparser.ConfigParser()
config_file = os.path.abspath(os.path.join('config', 'config_roybot.ini'))

try:
    dataset = config.read([config_file])
    if len(dataset) == 0:
        raise IOError
except IOError as e:
    print('Unable to open config file: ' + str(config_file))
    #self.logger.warning('Unable to open config file: ' + str(config_file))
    #self.before_quit()
except ConfigParser.Error as e:
    print('Error with config file: ' + str(config_file))
    # self.logger.warning('Error with config file: ' + str(config_file))
    # self.before_quit()

sqlite_file = os.path.abspath(config.get('files', 'sqlite_file'))
print(sqlite_file)

db = sqlite3.connect(sqlite_file)
db.row_factory = dict_factory
cursor = db.cursor()


class ActionRulerList(Action):
    def name(self) -> Text:
        return "action_ruler_list"

    async def run(self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # """Handles the intent where a question seeks a list of rulers in a particular group or potentially the first or last of such a group."""

        detail=False

        ### self.logger.info('Intent: ruler_list')
        # Core query: SELECT * FROM `ruler` WHERE xyz... ORDER BY date(ReignStartDt)
        # If all or first or last variant, must add:
        #   All:    ASC
        #   First:  ASC LIMIT 1
        #   Last:   DESC LIMIT 1
        
        # additional cases: if they list a year, then find ruler(s) in that year
        # SELECT * FROM ruler WHERE CAST(STRFTIME('%Y', ReignStartDt) AS INT) <= 1400 AND CAST(STRFTIME('%Y', ReignEndDt) AS INT) >= 1400
        sql = 'SELECT `Name`, `Number`, `RulerId`, `RulerType` FROM `ruler`'
        fields = ['Name', 'Number']
        country = None
        house = None
        position = None
        year = None
        century_start = None
        century_end = None
        ruler_type = None
        where = []
        params = {}
        sql_suffix = ' ORDER BY date(ReignStartDt)'

        ents = tracker.latest_message['entities']
        print(ents)

        for ent in ents:
            if ent['entity'].lower() in (
                    'ruler_type', 'country', 'location', 'house', 'year', 'year-words', 'period', 'position'):
                # self.logger.debug(
                #     'Selection entity found: ' + ent['value'] +
                #     ' (' + ent['entity'] + ')')
                if ent['entity'].lower() == 'ruler_type':
                    ruler_type = ent['value'].lower()
                    # TODO: consider breaking out this mapping into a generalised helper function
                    if ruler_type in ('king', 'kings', 'men', 'males'):
                        ruler_type = 'king'
                    if ruler_type in ('queen', 'queens', 'women', 'females'):
                        ruler_type = 'queen'
                    if ruler_type not in ('monarch', 'ruler', 'rulers', 'monarchs', 'leader', 'leaders'):  # or any other non-restricting ruler_types
                        where.append('RulerType = :RulerType')
                        params['RulerType'] = ruler_type
                if ent['entity'].lower() in ('country', 'location'):
                    # TODO: add ability to handle selection by one of a ruler's countries
                    #   (eg select by England only if ruler rules England and Scotland)
                    country = ent['value']
                    where.append('Country LIKE :Country')
                    params['Country'] = '%' + country + '%'

                if ent['entity'].lower() == 'house':
                    # TODO: make selection less brittle
                    house = ent['value']
                    where.append('House = :House')
                    params['House'] = house
                
                if ent['entity'].lower() in ('year', 'year-words'):
                    if ent['entity'].lower() == 'year':
                        year = ent['value']
                    else:
                        year = map_entity_to_number(ent) # ie year-words
                    where.append("CAST(STRFTIME('%Y', ReignStartDt) AS INT) <= :Year AND CAST(STRFTIME('%Y', ReignEndDt) AS INT) >= :Year")
                    params['Year'] = year

                if ent['entity'].lower() == 'period':
                    if ent['value'].lower() == 'century':
                        for n in ents:
                            if n['entity'].lower() in (
                                    'number', 'number-roman', 'nth',
                                    'nth-words', 'number-words'):
                                num = map_entity_to_number(n)
                                if num is not None:
                                    century_end = int(num) * 100
                                    century_start = century_end - 100
                                    where.append("CAST(STRFTIME('%Y', ReignStartDt) AS INT) <= :CenturyEnd AND CAST(STRFTIME('%Y', ReignEndDt) AS INT) >= :CenturyStart")
                                    params['CenturyEnd'] = century_end
                                    params['CenturyStart'] = century_start

                if ent['entity'].lower() == 'position':
                    position = ent['value'].lower()
                    # TODO: expand this to cope with second, third etc of
                    if position in ('first', 'earliest', 'start', 'beginning'):
                        sql_suffix = sql_suffix + ' ASC LIMIT 1'
                    if position in ('last', 'latest', 'final', 'end'):
                        sql_suffix = sql_suffix + ' DESC LIMIT 1'
        # if ruler_type is not None:
        #     self.logger.debug('Ruler Type: ' + str(ruler_type))
        # if country is not None:
        #     self.logger.debug('Country: ' + str(country))
        # if house is not None:
        #     self.logger.debug('House: ' + str(house))
        if position is not None:
            print('Position: ' + str(position))
        else:
            sql_suffix = sql_suffix + ' ASC'
        if where:
            sql = '{} WHERE {}'.format(sql, ' AND '.join(where))
            sql = sql + sql_suffix
        print('SQL: ' + sql)
        print('Params: ' + str(params))
        try:
            cursor.execute(sql, params)
        except sqlite3.Error as e:
            dispatcher.utter_message(text = 'I experienced a problem answering that question. Could we try another question instead?')
            return
        output = ''
        results = cursor.fetchall()
        last_ruler_count = len(results)
        print(f'{last_ruler_count = }')
        if last_ruler_count == 1:
            last_ruler_id = str(results[0]['RulerId'])
            print(f'Set {last_ruler_id =}')
        else:
            last_ruler_id = None
            if last_ruler_count == 0:
                if self.name() == "action_ruler_pronoun_feature":
                    dispatcher.utter_message(text ='I am not aware of a recently referenced ruler. Try asking about a specific person (eg Elizabeth the First).')
                else:
                    dispatcher.utter_message(text ='Based on my understanding of your question, I am not able to match any rulers. You may have a typo or a non-existent combination (eg Richard the Seventh).')
            if (position is not None) and (last_ruler_count > 1):
                dispatcher.utter_message(text ='It looks like you were after a specific ruler, but I am matching several (so perhaps something went wrong, either with how the question was asked or how I understood it).')
                dispatcher.utter_message(text ='Here they are anyway:')

        print(f'{results=} {len(results)=}')

        for row in results:
            row = format_row(row)
            print(row["Name"])
            #output = output + merge_output(row) + '\n'
            output = output + f'{row["Name"]} {row["Number"]}.\n'

        dispatcher.utter_message(text = f'{output}')
        return [SlotSet("last_ruler_id", last_ruler_id)]


class ActionRulerCombinedBeforeAfter(Action):
    def name(self) -> Text:
        return "action_ruler_combined_before_after"

    async def run(self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        print(f'Intent: {self.name()}')
        before = self.name() == "action_ruler_before"

        ## Before
        # SELECT *
        # FROM ruler
        # WHERE RulerId < (SELECT RulerId FROM ruler WHERE Name = 'Henry' AND `Number` = '8')
        # ORDER BY RulerId DESC
        # LIMIT 1

        ## After
        # SELECT *
        # FROM ruler
        # WHERE RulerId > (SELECT RulerId FROM ruler WHERE Name = 'Henry' AND `Number` = '8')
        # ORDER BY RulerId
        # LIMIT 1

        sql = "SELECT `Name`, `Number`, `RulerId`, `RulerType` FROM ruler WHERE RulerId "
        sql_middle = " (SELECT RulerId FROM ruler"
        
        if before:
            sql = sql + '<' + sql_middle
            sql_suffix = "ORDER BY RulerId DESC LIMIT 1"
        else:
            # after
            sql = sql + '>' + sql_middle
            sql_suffix = "ORDER BY RulerId LIMIT 1"

        fields = ['Name', 'Number']

        num = None
        loc = None
        ruler_type = None

        where = []
        sub_where = []
        params = {}
        ents = tracker.latest_message['entities']
        for ent in ents:
            if ent['entity'].lower() in (
                    'name', 'location', 'number', 'number-words',
                    'number-roman', 'nth-words', 'nth', 'title','ruler_type'):
                # self.logger.debug(
                #     'Selection entity found: ' + ent['value'] +
                #     ' (' + ent['entity'] + ')')
                if ent['entity'].lower() == 'ruler_type':
                    ruler_type = ent['value'].lower()
                    # TODO: consider breaking out this mapping into a generalised helper function
                    if ruler_type in ('king', 'kings', 'men', 'males'):
                        ruler_type = 'king'
                    if ruler_type in ('queen', 'queens', 'women', 'females'):
                        ruler_type = 'queen'
                    if ruler_type not in ('monarch', 'ruler', 'rulers', 'monarchs', 'leader', 'leaders'):  # or any other non-restricting ruler_types
                        where.append('RulerType = :RulerType')
                        params['RulerType'] = ruler_type
                if ent['entity'].lower() == 'name':
                    name = ent['value']
                    sub_where.append('Name = :Name')
                    params['Name'] = name
                if ent['entity'].lower() == 'title':
                    title = ent['value']
                    sub_where.append('Title = :Title')
                    params['Title'] = title
                if ent['entity'].lower() == 'location':
                    loc = ent['value']
                    sub_where.append('Country LIKE :Location')
                    params['Location'] = '%' + loc + '%'
                if ent['entity'].lower() in (
                        'number', 'number-roman', 'nth',
                        'nth-words', 'number-words'):
                    num = map_entity_to_number(ent)
                    if num is not None:
                        sub_where.append('Number = :Number')
                        params['Number'] = num

        # if loc is not None:
        #     self.logger.debug('Loc: ' + str(loc))
        # if num is not None:
        #     self.logger.debug('Num: ' + str(num))
        if where:
            sql_suffix = ") AND {} ".format(' AND '.join(where)) + sql_suffix
        else:
            sql_suffix = ") " + sql_suffix
        if sub_where:
            sql = '{} WHERE {}'.format(sql, ' AND '.join(sub_where))
            sql = sql + sql_suffix
        print('SQL: ' + sql)
        print('Params: ' + str(params))
        try:
            cursor.execute(sql, params)
        except sqlite3.Error as e:
            dispatcher.utter_message(text = 'I experienced a problem answering that question. Could we try another question instead?')
            return
        output = ''
        results = cursor.fetchall()
        last_ruler_count = len(results)
        print(f'{last_ruler_count = }')
        #self.user['last_ruler_count'] = len(results)
        if last_ruler_count == 1:
            last_ruler_id = str(results[0]['RulerId'])
            print(f'Set {last_ruler_id =}')
        else:
            last_ruler_id = None
            if last_ruler_count == 0:
                if self.name() == "action_ruler_pronoun_feature":
                    dispatcher.utter_message(text ='I am not aware of a recently referenced ruler. Try asking about a specific person (eg Elizabeth the First).')
                else:
                    dispatcher.utter_message(text ='Based on my understanding of your question, I am not able to match any rulers. You may have a typo or a non-existent combination (eg Richard the Seventh).')
            else:
                dispatcher.utter_message(text = 'Based on my understanding of your question, I\'m having trouble narrowing down the selection to a single ruler. You may need to be a little more specific.')
            return [SlotSet("last_ruler_id", last_ruler_id)]

        for row in results:
            row = format_row(row)
            print(row)
            #output = merge_output(row)
            output = output + f'{row["Name"]} {row["Number"]}.\n'
        #dispatcher.utter_message(text = f'The ruler before after was run based on {self.name()}.')
        dispatcher.utter_message(text = f'{output}')
        return [SlotSet("last_ruler_id", last_ruler_id)]


class ActionRulerBefore(ActionRulerCombinedBeforeAfter):
    """Class inherits from ActionRulerCombinedBeforeAfter because the vast majority of the class functionality required is the same
    whether it's a before and an after scenario.
    Simply inherit and then add a few checks within the combined class where they need to act differently."""
    def name(self) -> Text:
        return "action_ruler_before"


class ActionRulerAfter(ActionRulerCombinedBeforeAfter):
    """Class inherits from ActionRulerCombinedBeforeAfter because the vast majority of the class functionality required is the same
    whether it's a before and an after scenario.
    Simply inherit and then add a few checks within the combined class where they need to act differently."""
    def name(self) -> Text:
        return "action_ruler_after"




class ActionExample(Action):
    def name(self) -> Text:
        return "action_example"

    async def run(self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        example_list = random.choice([
            'In the House of Anjou who was the last ruler?',
            'Tell me all about Henry the Eighth',
            'Who was king after Richard the Lionheart?',
            'What date was Elizabeth the First born?',
            'What were the circumstances of Edward the Second\'s death?',
            'What can I say?'
            ])

        suggestion_intro = random.choice([
            'Here\'s an example to try:\n\t',
            'How about this?\n\t',
            'Give this a go!\n\t'])

        dispatcher.utter_message(text = f'{suggestion_intro} {example_list}')
        return []


class ActionRulerFeature(Action):
    def name(self) -> Text:
        return "action_ruler_feature"

    async def run(self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        
        #TODO: fix this based on the royboy.py code
        detail = False

        #name = tracker.get_slot('name')
        #name = next(tracker.get_latest_entity_values("name"), None)
        #features = list(tracker.get_latest_entity_values("feature"))
        #print(features)
        ents = tracker.latest_message['entities']
        print(ents)

        sql = 'SELECT DISTINCT {fields} FROM `ruler`'
        
        num = None
        loc = None
        fields = []
        where = []
        params = {}
        for ent in ents:
            if ent['entity'].lower() in (
                    'name', 'location', 'number', 'number-words',
                    'number-roman', 'nth-words', 'nth', 'title'):
                # self.logger.debug(
                #     'Selection entity found: ' + ent['value'] +
                #     ' (' + ent['entity'] + ')')
                if ent['entity'].lower() == 'name':
                    name = ent['value']
                    where.append('Name = :Name')
                    params['Name'] = name
                if ent['entity'].lower() == 'title':
                    title = ent['value']
                    where.append('Title = :Title')
                    params['Title'] = title
                if ent['entity'].lower() == 'location':
                    loc = ent['value']
                    where.append('Country LIKE :Location')
                    params['Location'] = '%' + loc + '%'
                if ent['entity'].lower() in (
                        'number', 'number-roman', 'nth',
                        'nth-words', 'number-words'):
                    num = map_entity_to_number(ent)
                    if num is not None:
                        where.append('Number = :Number')
                        params['Number'] = num
            else:
                if not detail:
                    # self.logger.info(
                    #     'A field related entity was found: ' +
                    #     ent['value'] + ' (' + ent['entity'] + ')')
                    f = map_feature_to_field(ent['value'])
                    if (f is not None) & (f not in fields):
                        fields = fields + f
            #print(f'fields: {str(fields)}')
        
        print(f'{self.name() =}')
        if self.name() == "action_ruler_pronoun_feature":
            where = ["RulerId = :RulerId"]
            params['RulerId'] = tracker.get_slot('last_ruler_id')

        if 'RulerId' not in fields:
            fields.append('RulerId')
        if 'RulerType' not in fields:
            fields.append('RulerType')
        if 'Portrait' in fields:
            fields.append('Name')
            fields.append('Number')
        # self.logger.debug('Fields: ' + str(fields))
        # if overload_item is not None:
        #     self.logger.debug('Overload item: ' + str(overload_item))
        # if loc is not None:
        #     self.logger.debug('Loc: ' + str(loc))
        # if num is not None:
        #     self.logger.debug('Num: ' + str(num))
        if fields:
            sql = sql.format(fields=', '.join(fields))
        else:
            sql = sql.format(fields='*')
        if where:
            sql = '{} WHERE {}'.format(sql, ' AND '.join(where))
        print('SQL: ' + sql)
        print('Params: ' + str(params))
        try:
            cursor.execute(sql, params)
        except sqlite3.Error as e:
            dispatcher.utter_message(text = 'I experienced a problem answering that question. Could we try another question instead?')
            return []
        output = ''
        results = cursor.fetchall()
        last_ruler_count = len(results)
        print(f'{last_ruler_count = }')
        # self.logger.debug('Last ruler count: ' + str(self.user['last_ruler_count']))
        if last_ruler_count == 1:
            last_ruler_id = str(results[0]['RulerId'])
            print(f'Set {last_ruler_id =}')
        else:
            last_ruler_id = None
            if last_ruler_count == 0:
                if self.name() == "action_ruler_pronoun_feature":
                    dispatcher.utter_message(text ='I am not aware of a recently referenced ruler. Try asking about a specific person (eg Elizabeth the First).')
                else:
                    dispatcher.utter_message(text ='Based on my understanding of your question, I am not able to match any rulers. You may have a typo or a non-existent combination (eg Richard the Seventh).')
            else:
                dispatcher.utter_message(text ='Based on my understanding of your question, I cannot narrow down the selection to a single ruler. You may need to be a little more specific.')
            return [SlotSet("last_ruler_id", last_ruler_id)]
        reply = ''
        print(f'{results=}')
        for row in results:
            row = format_row(row)
 
        #dispatcher.utter_message(text = f"{', '.join(fields)}:\n{params}\n{reply}")
        #dispatcher.utter_message(text = f"SQL generated is:\n{sql}\nParameters are:\n{params}\n{reply}")
        #dispatcher.utter_message(text = f"{reply}\nSQL generated is:\n{sql}")
        #kw = {'Portrait':'Victoria'}
        print(f'{fields[0] =}')
        pronouns = ruler_gender_pronouns[results[0]['RulerType']]
        results[0].update(pronouns)
        if fields[0] == 'Portrait':
             print(f'Portrait: {results[0]["Portrait"]}')
             dispatcher.utter_message(text = f'A picture of {results[0]["Name"]} {results[0]["Number"]}.', image = results[0]['Portrait'])
             #dispatcher.utter_message(response = 'utter_ruler_feature_Portrait', **results[0], image = results[0]['Portrait'])
             return [SlotSet("last_ruler_id", last_ruler_id)]
        if len(fields) > 5:
            utterance_built = 'utter_ruler_feature_all'
        else:
            utterance_built = 'utter_ruler_feature_' + fields[0]
        print(f'{utterance_built =}')
        dispatcher.utter_message(response = utterance_built, **results[0])
        return [SlotSet("last_ruler_id", last_ruler_id)]


class ActionRulerPronounFeature(ActionRulerFeature):
    """Class inherits from ActionRulerCombinedBeforeAfter because the vast majority of the class functionality required is the same
    whether it's a before and an after scenario.
    Simply inherit and then add a few checks within the combined class where they need to act differently."""
    def name(self) -> Text:
        return "action_ruler_pronoun_feature"