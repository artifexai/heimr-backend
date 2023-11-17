import sys

import pandas as pd
from dotenv import load_dotenv

from utils.paths import get_root_directory

sys.path.append(get_root_directory())

if __name__ == '__main__':
    from database import Properties, build_session

    load_dotenv()

    properties = pd.read_csv(f'{get_root_directory()}/data/sample_master_property_list.csv')

    properties['property_id'] = properties['realtor_property_id']
    properties.drop('realtor_property_id', inplace=True, axis=1)

    properties['zip_code'] = properties['zip_code'].astype(str).str.zfill(5)

    properties['last_sold_date'] = pd.to_datetime(properties['last_sold_date'], format="%m/%d/%y").dt.date

    prob = None
    er = None
    n_added = 0

    with build_session() as sess:
        sess.query(Properties).delete()

        sess.commit()

        properties_recs = [Properties(**i) for i in properties.to_dict(orient='records')]

        for p in properties_recs:
            p.parse()
            sess.add(p)
            try:
                sess.commit()
                n_added += 1
            except Exception as e:
                sess.rollback()
                prob = p
                er = e
                break
        sess.commit()

        print(f'Added {n_added} properties')
