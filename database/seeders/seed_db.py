import sys
import arrow
import pandas as pd
import re
from utils.paths import get_root_directory
from dotenv import load_dotenv

sys.path.append(get_root_directory())

if __name__ == '__main__':
    from database import Tax, Listing, Permit, build_session
    load_dotenv()

    listings = pd.read_csv(f'{get_root_directory()}/data/sample_listings.csv')
    permits = pd.read_csv(f'{get_root_directory()}/data/sample_permit_data.csv').drop(columns=['UnitNumber'])
    taxes = pd.read_csv(f'{get_root_directory()}/data/sample_tax_history.csv')


    def drop_unnamed(df):
        return df[[i for i in df.columns if 'unnamed' not in str(i).lower()]]


    def to_snake(_string):
        return re.compile(r'(?<!^)(?=[A-Z])').sub('_', _string).lower().replace(' _', '_')


    def try_parse_date(d):
        try:
            return arrow.get(d).datetime
        except:
            return None


    listings = drop_unnamed(listings)
    permits = drop_unnamed(permits)
    taxes = drop_unnamed(taxes)

    listings.columns = [to_snake(c) for c in listings.columns]
    permits.columns = [to_snake(c) for c in permits.columns]
    taxes.columns = [to_snake(c) for c in taxes.columns]

    prob = None
    er = None
    n_added = 0

    with build_session() as sess:
        sess.query(Listing).delete()
        sess.query(Permit).delete()
        sess.query(Tax).delete()
        sess.commit()

        listing_recs = [Listing(**i) for i in listings.to_dict(orient='records')]
        permit_recs = [Permit(**i) for i in permits.to_dict(orient='records')]
        tax_recs = [Tax(**i) for i in taxes.to_dict(orient='records')]

        for l in listing_recs:
            l.parse()
            sess.add(l)
            try:
                sess.commit()
                n_added += 1
            except Exception as e:
                sess.rollback()
                prob = l
                er = e
                break
        sess.commit()

        print(f'Added {n_added} Listings')
        n_added = 0

        for r in permit_recs:
            r.parse()
            sess.add(r)
            try:
                sess.commit()
                n_added += 1
            except Exception as e:
                sess.rollback()
                prob = r
                er = e
                break
        sess.commit()

        print(f'Added {n_added} permits')
        n_added = 0

        for t in tax_recs:
            t.parse()
            sess.add(t)
            try:
                sess.commit()
                n_added += 1
            except Exception as e:
                sess.rollback()
                prob = t
                er = e
                break

        sess.commit()
        print(f'Added {n_added} tax records')
