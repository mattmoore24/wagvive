#!/usr/bin/env python3
"""Round-4 manifest: freight-verified pricing for every variant we intend to
list. Fails loudly if any retail sits under the 50% floor or a freight quote
is estimated (a $0/missing quote is missing data, never free carriage)."""
import json, sys
sys.path.insert(0, 'config')
import cj_api, freight_floor
from pricing import landed, FLAT, PCT, SALES_TAX_AVG, DUTY_PCT

FEE = PCT * (1 + SALES_TAX_AVG)
FLOOR = 0.50


def need_for(vid, cost):
    fr = cj_api.call('/logistic/freightCalculate', payload={
        'startCountryCode': 'CN', 'endCountryCode': 'US',
        'products': [{'quantity': 1, 'vid': vid}]})
    price, carrier, aging, est = freight_floor.resolve(fr.get('data'))
    need = (landed(cost, price, DUTY_PCT) + FLAT) / (1 - FEE - FLOOR)
    return need, price, carrier, est


MANIFEST = {
 'sneaker':  {'title': 'Wagvive Sneaker Chew Buddy', 'opt': 'Color', 'price': {'*': '16.99'},
    'vars': [('CJYD252933701AZ', 'Yellow'), ('CJYD252933702BY', 'Black'), ('CJYD252933703CX', 'Sea Fog Blue')]},
 'ringball': {'title': 'Wagvive Jingle Plush Ball', 'opt': 'Character', 'price': {'*': '19.99'},
    'vars': [('CJST257870801AZ', 'Monkey'), ('CJST257870802BY', 'Frog'), ('CJST257870803CX', 'Dog')]},
 'teddy':    {'title': 'Wagvive Cuddle Companion Teddy', 'opt': None, 'price': {'*': '19.99'},
    'vars': [('CJYD245411401AZ', 'Default Title')]},
 'vocalplush': {'title': 'Wagvive Corduroy Squeak Pals', 'opt': 'Character', 'price': {'*': '19.99'},
    'vars': [('CJMY126277901AZ', 'Fawn'), ('CJMY126277902BY', 'Crooked Neck'), ('CJMY126277903CX', 'Frog')]},
 'chicken':  {'title': 'Wagvive Screaming Chicken', 'opt': 'Color', 'price': {'*': '24.99'},
    'vars': [('CJST258510901AZ', 'Green'), ('CJST258510902BY', 'Orange'), ('CJST258510903CX', 'Black')]},
 'towel':    {'title': 'Wagvive Quick-Dry Bath Robe', 'opt': ('Color', 'Size'),
    'price': {'XS': '18.99', 'S': '21.99', 'M': '23.99'},
    'vars': [('CJGY138841301AZ', 'Blue', 'XS'), ('CJGY138841302BY', 'Blue', 'S'), ('CJGY138841303CX', 'Blue', 'M'),
             ('CJGY138841304DW', 'Pink', 'XS'), ('CJGY138841305EV', 'Pink', 'S'), ('CJGY138841306FU', 'Pink', 'M'),
             ('CJGY138841307GT', 'Green', 'XS'), ('CJGY138841308HS', 'Green', 'S'), ('CJGY138841309IR', 'Green', 'M')]},
 'lednail':  {'title': 'Wagvive LED Nail Clippers', 'opt': 'Color', 'price': {'*': '27.99'},
    'vars': [('CJYD226496002BY', 'Green'), ('CJYD226496003CX', 'Pink'), ('CJYD226496004DW', 'White')]},
 'dematting': {'title': 'Wagvive Dematting Comb', 'opt': None, 'price': {'*': '18.99'},
    'vars': [('CJYD275409401AZ', 'Default Title')]},
 'pawtrimmer': {'title': 'Wagvive Cordless Paw Trimmer', 'opt': None, 'price': {'*': '39.99'},
    'vars': [('CJNP222636501AZ', 'Default Title')]},
 'pawcup':   {'title': 'Wagvive Paw Washing Cup', 'opt': ('Color', 'Size'),
    'price': {'S': '17.99', 'M': '18.99', 'L': '19.99'},
    'vars': [('CJSP293469601AZ', 'Blue', 'S'), ('CJSP293469603CX', 'Blue', 'M'), ('CJSP293469605EV', 'Blue', 'L'),
             ('CJSP293469607GT', 'Orange', 'S'), ('CJSP293469609IR', 'Orange', 'M'), ('CJSP293469611KP', 'Orange', 'L'),
             ('CJSP293469613MN', 'Green', 'S'), ('CJSP293469615OL', 'Green', 'M'), ('CJSP293469617QJ', 'Green', 'L')]},
 'wblanket': {'title': 'Wagvive Waterproof Snuggle Blanket', 'opt': ('Color', 'Size'),
    'price': {'XS': '22.99', 'S': '32.99'},
    'vars': [('CJGY192649701AZ', 'Black', 'XS'), ('CJGY192649702BY', 'Black', 'S'),
             ('CJGY192649706FU', 'Gray', 'XS'), ('CJGY192649707GT', 'Gray', 'S'),
             ('CJGY192649711KP', 'Coffee', 'XS'), ('CJGY192649712LO', 'Coffee', 'S')]},
 'thunder':  {'title': 'Wagvive Calming Thunder Wrap', 'opt': 'Color', 'price': {'*': '36.99'},
    'vars': [('CJYD264078601AZ', 'Grey'), ('CJYD264078602BY', 'Dark Blue'), ('CJYD264078603CX', 'Grey and Blue')]},
 'heartbeat': {'title': 'Wagvive Heartbeat Soothing Sloth', 'opt': None, 'price': {'*': '43.99'},
    'vars': [('CJYD233940102BY', 'Default Title')]},
 'fleece':   {'title': 'Wagvive Paw Print Fleece Blanket', 'opt': ('Color', 'Size'),
    'price': {'S': '15.99', 'M': '19.99'},
    'vars': [('CJGY211711303CX', 'Camel', 'S'), ('CJGY211711304DW', 'Camel', 'M'),
             ('CJGY211711310JQ', 'Beige', 'S'), ('CJGY211711311KP', 'Beige', 'M'),
             ('CJGY211711317QJ', 'Pink', 'S'), ('CJGY211711318RI', 'Pink', 'M')]},
}


def main():
    picks = json.load(open('config/round4_picks_variants.json'))
    costs, vids = {}, {}
    for key, info in picks.items():
        d = cj_api.call('/product/query', {'productSku': info['spu']}).get('data') or {}
        for v in (d.get('variants') or []):
            costs[(key, v.get('variantSku'))] = float(v.get('variantSellPrice') or 0)
            vids[(key, v.get('variantSku'))] = v.get('vid')

    print(f"{'product':12}{'variant':26}{'cost':>7}{'need':>8}{'price':>8}  status")
    fails, results = [], {}
    for key, m in MANIFEST.items():
        results[key] = {'title': m['title'], 'opt': m['opt'],
                        'spu': picks[key]['spu'], 'variants': []}
        for var in m['vars']:
            sku = var[0]
            size = var[2] if len(var) > 2 else '*'
            price = float(m['price'].get(size, m['price'].get('*', 0)))
            if (key, sku) not in costs:
                print(f"{key:12}{sku:26}  MISSING AT CJ"); fails.append((key, sku, 'missing')); continue
            need, fr, carrier, est = need_for(vids[(key, sku)], costs[(key, sku)])
            ok = price >= need and not est
            if not ok: fails.append((key, sku, f'need {need:.2f} vs {price}'))
            print(f"{key:12}{sku:26}{costs[(key, sku)]:7.2f}{need:8.2f}{price:8.2f}  {'OK' if ok else 'FAIL'} ({carrier[:18]})")
            results[key]['variants'].append({'sku': sku, 'opts': list(var[1:]),
                'cost': costs[(key, sku)], 'need': round(need, 2),
                'price': f'{price:.2f}', 'freight': fr, 'carrier': carrier})
    json.dump(results, open('config/round4_manifest.json', 'w'), indent=1)
    print('\nFAILS:', fails if fails else 'none')
    print('saved -> config/round4_manifest.json')


if __name__ == '__main__':
    main()
