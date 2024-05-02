# """Module for representing a Castor grid cell in Python."""
# import typing
# from castoredc_api.study.castor_objects.castor_data_point import CastorDataPoint
# from castoredc_api.study.castor_study import CastorStudy


# class CastorGridCell(CastorDataPoint):
#     """Object representing a Castor grid cell.
#     Inherits from the CastorDataPoint class to use its interpretation
#     functions to interpret cells of a Castor grid data point."""

#     def __init__(
#         self,
#         field_id: str,
#         field_name: str,
#         raw_value: typing.Union[str, int],
#         field_type: str,
#         option_group: str,
#         study: "CastorStudy",
#     ) -> None:
#         """Creates a CastorGridDataPoint."""
#         self.field_id = field_id
#         self.raw_value = raw_value
#         self.isntance_of.field_name = field_name + " - grid object"
#         self.instance_of.field_type = field_type
#         self.instance_of.field_option_group = option_group
#         self.value = self.__interpret(study)
