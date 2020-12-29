#! python3
# antiretroviral_finder.py - searches for complicated combination drugs, says if
#                               they're in, stock, finds ways to "build" them,
#                                   or tells the user if it will be impossible


import json
import logging
import os
from pathlib import Path
import time


class Drug_Library():

    def __init__(self):
        try:
            with open('arvt_dic.json', 'r') as infile:
                self.drug_dic = json.load(infile)
            logging.debug(f'drug_dic loaded from arvt_dic.json')

        except Exception as e:
            print(f'\n{e}: Cannot open drug library.')
            enter_to_quit()

        self.stocked_drugs = {}
        for brand_name, strengths in self.drug_dic.items():
            stocked_strengths = []
            for strength in strengths:
                if strength['on hand'] is True:
                    strength = strength.copy()
                    del strength['on hand']
                    stocked_strengths.append(strength)

            if stocked_strengths:
                self.stocked_drugs[brand_name] = stocked_strengths

        logging.debug(f'len(self.stocked_drugs) == {len(self.stocked_drugs)}')
        return


def show_title():
    title = ' ANTIRETROVIRAL FINDER '
    bar = '*' * len(title)
    print(f'\n{bar}\n{title}\n{bar}')
    return


def enter_to_quit():
    input('\nPress ENTER to quit...')
    quit()


def give_menu_options(lst):
    lst += ['None of these']
    for i, v in enumerate(lst):
        print(f'{i+1}. {v}')

    while True:
        idx = input('\nPlease choose a number above: ')
        try:
            idx = int(idx) - 1
            if idx == i:
                return None
            else:
                return idx - 1
        except ValueError:
            print("I didn't understand that choice. Please try again.")


def get_user_search(Drug_Library):
    drug_dic = Drug_Library.drug_dic
    stocked_drugs = Drug_Library.stocked_drugs

    while True:
        user_search = ''
        user_search = input('\nEnter the BRAND name of the antiretroviral you are looking for: ')
        user_search = user_search.lower().strip()

        if user_search == '':
            return None
        elif user_search in drug_dic.keys():
            return user_search

        possible_matches = [drug.title() for drug in drug_dic.keys() if drug.startswith(user_search[0])]
        if possible_matches:
            possible_matches += ['None of these']
            print('\nDid you mean:')
            choice = give_menu_options(possible_matches)
            if choice != 'none of these':
                return choice

        else:
            print(f"Couldn't find {user_search.title()}. Please try again.")


def see_if_missing_parts(needed_parts, drugs_found):
    missing_parts = {}
    for drug, dose in needed_parts.items():
        if drug not in drugs_found:
            missing_parts[drug] = dose
    return missing_parts


def dic_to_string(brand_name, strengths):
    drugs = [drug for drug in strengths.keys() if drug != 'on hand']
    doses = [str(dose) for dose in strengths.values() if not isinstance(dose, bool)]
    return f"{'/'.join(drugs)} {'/'.join(doses)}mg ({brand_name.title()})"


def find_alt_parts(Drug_Library, missing_parts):
    stocked_drugs = Drug_Library.stocked_drugs

    alt_parts = {}
    for drug in missing_parts:
        for brand_name, strengths in stocked_drugs.items():
            for strength in strengths:
                if len(strength) == 1:
                    if drug in strength.keys() or drug + ' fumarate' in strength.keys():
                        alt_parts[brand_name] = strength

    if alt_parts:
        print('\nThe following drugs may contain missing strengths and/or different salt forms:')
        for brand_name, strengths in alt_parts.items():
            print(f' - {dic_to_string(brand_name, strengths)}')


def find_parts(Drug_Library, drug_name):
    drug_dic = Drug_Library.drug_dic
    stocked_drugs = Drug_Library.stocked_drugs

    local_dic = drug_dic.copy()
    local_stock = stocked_drugs.copy()

    known_strengths = local_dic[drug_name]

    if len(known_strengths) > 1:
        print(f'\nMultiple strengths exist for {drug_name.title()}:')
        choices = []
        for strength in known_strengths:
            choices.append(dic_to_string(drug_name.title(), strength))

        choice = give_menu_options(choices)
        if choice:
            strength_needed = local_dic[drug_name][choice]
        else:
            return

    else:
        strength_needed = local_dic[drug_name][0]

    try:
        del strength_needed['on hand']
    except KeyError:
        pass # FIXME surely there is a better way to do this?

    print(f'\nSearching for {dic_to_string(drug_name, strength_needed)}...')
    time.sleep(0.5)

    if drug_name in local_stock.keys():
        print(f'\n{drug_name.title()} should be on-hand.')
        return

    found_parts = {}
    for brand_name, strengths in local_stock.items():
        for strength in strengths:
            if strength.items() <= strength_needed.items():
                found_parts[brand_name] = strength

    drugs_found = []
    for parts in found_parts.values():
        for drug in parts.keys():
            if drug not in drugs_found:
                drugs_found.append(drug)

    missing_parts = see_if_missing_parts(strength_needed, drugs_found)

    if missing_parts:
        for drug, dose in missing_parts.items():
            for brand_name, strengths in local_stock.items():
                for strength in strengths:
                    if len(strength) == 1 and drug in strength.keys():
                        for med, mg in strength.items():
                            if dose % mg in [0, 0.5]:
                                found_parts[brand_name] = {med: mg}
                                drugs_found.append(med)

    missing_parts = see_if_missing_parts(strength_needed, drugs_found)

    if not found_parts:
        print(f'\nDid not find any on-hand parts of {drug_name.title()}.')
        find_alt_parts(Drug_Library, missing_parts)
        return

    elif missing_parts:
        print(f'\nNot all parts of {drug_name.title()} may be on hand.')

        print('\nStocked parts:')
        for brand_name, strengths in found_parts.items():
            print(f' - {dic_to_string(brand_name, strengths)}')

        print('Missing parts:')
        for drug, dose in missing_parts.items():
            print(f' - {drug} {dose}mg')

        find_alt_parts(Drug_Library, missing_parts)
        return

    else:
        print(f'\nYou should be able to make {drug_name.title()} out of the following on-hand drugs:')
        for brand_name, strengths in found_parts.items():
            print(f' - {dic_to_string(brand_name, strengths)}')

        return


def main():
    os.chdir(Path(__file__).parent)

    logging.debug(f'Path(__file__) = {Path(__file__)}')
    logging.debug(f'os.getcwd() = {os.getcwd()}')

    drug_library = Drug_Library()
    while True:
        try:
            show_title()
            # test with triumeq, biktarvy, preztiza, symtuza FIXME triumeq broken
            user_search = get_user_search(drug_library)
            if user_search:
                find_parts(drug_library, user_search)
                input('\nPress ENTER to continue...')

        except KeyboardInterrupt:
            enter_to_quit()


logging.basicConfig(level=logging.DEBUG, format=' - %(levelname)s - %(message)s')
logging.disable(logging.CRITICAL)

main()
