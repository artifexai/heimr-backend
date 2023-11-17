from typing import Optional, List, Type

from fastapi import APIRouter, Depends
from sqlalchemy.orm import noload

from api.dependencies import app_db
from api.shared_data import get_search_idx
from database import Permit, PropertyDB, DBSessionType, ListingDB, TaxDB
from models.listing import ListingStruct
from models.property import PropertyStruct
from models.tax import TaxStruct

router = APIRouter(dependencies=[Depends(app_db)])


@router.get("/properties")
async def get_properties(q: Optional[str] = None, db: DBSessionType = Depends(app_db)):
    """
    Performs a search for properties matching the given query 'q'.

    Parameters
    ----------
    q: str - search query
    db: DBSessionType - database session

    Returns
    -------
    List[Dict]

    """

    if not q:
        props_with_listings: List[Type[PropertyDB]] = (
            db.query(PropertyDB)
            .join(PropertyDB.address)
            .limit(10)
            .options(noload(PropertyDB.tax), noload(PropertyDB.listing))
            .all()
        )
        return [PropertyStruct.validate(prop) for prop in props_with_listings]

    idx = get_search_idx()
    matching_ids = idx.search(q)
    if not matching_ids:
        return []

    matching_ids = [int(i) for i in matching_ids]

    results: List[Type[PropertyDB]] = (
        db.query(PropertyDB)
        .join(PropertyDB.address)
        .filter(PropertyDB.property_id.in_(matching_ids))
        .limit(10)
        .options(noload(PropertyDB.tax), noload(PropertyDB.listing))
        .all()
    )

    if not results:
        return []

    properties = [PropertyStruct.validate(result) for result in results]
    return properties


@router.get("/listings/{property_id}")
async def get_listings(property_id: int, db: DBSessionType = Depends(app_db)):
    """
    An asynchronous API endpoint that fetches all the listings from the database.
    """

    listings = db.query(ListingDB).filter(ListingDB.property_id == property_id).all()

    if not listings:
        return []

    return [ListingStruct.validate(result) for result in listings]


@router.get("/permits/{lid}")
async def get_permits(lid: int, db: DBSessionType = Depends(app_db)):
    """
     An asynchronous API endpoint that fetches all the permits associated with a specific
    listing ID from the database.
    """

    permits = db.query(Permit).filter(Permit.listing_id == lid).all()

    permits = [permit.to_dict() for permit in permits]

    return {"permits": permits}


@router.get("/taxes/{property_id}")
async def get_tax(property_id: int, db: DBSessionType = Depends(app_db)):
    """
     An asynchronous API endpoint that fetches all the tax information associated with a specific
    listing ID from the database.
    """

    tax = db.query(TaxDB).where(TaxDB.property_id == property_id).all()
    return [TaxStruct.validate(t) for t in tax]
