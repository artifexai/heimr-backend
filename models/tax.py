from typing import Optional, Dict, List

from pydantic import BaseModel, Field, root_validator


class TaxStruct(BaseModel):
    property_id: int = Field()
    realtor_id: str = Field()

    year: int = Field()
    tax: int = Field()
    building: Optional[int] = Field()
    land: Optional[int] = Field()
    assessment: Optional[int] = Field()

    tax_id: Optional[int] = Field()

    class Config:
        orm_mode = True
        from_attributes = True

    @root_validator(pre=True)
    def preprocess(cls, data: Dict):
        if isinstance(data.get('assessment'), Dict):
            _as = data.pop('assessment')
            data['building'] = _as.pop('building')
            data['land'] = _as.pop('land')
            data['assessment'] = _as.pop('total')
            return data
        return data

    @staticmethod
    def from_raw_list(data: List[Dict], property_id: int, realtor_id: str) -> List['TaxStruct']:
        records = []
        for d in data:
            if not d['tax']:
                continue
            d.update({'property_id': property_id, 'realtor_id': realtor_id})
            records.append(TaxStruct.parse_obj(d))

        return records
