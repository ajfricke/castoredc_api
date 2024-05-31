"""Module for representing a Castor datapoint in Python."""
from datetime import datetime
import json
import typing
import numpy as np
import pandas as pd
from castoredc_api import CastorException
#from castoredc_api.study.castor_objects.castor_grid_cell import CastorGridCell
from castoredc_api.study.castor_objects.castor_field import CastorField

if typing.TYPE_CHECKING:
    
    from castoredc_api.study.castor_study import CastorStudy


class CastorDataPoint:
    """Object representing a Castor datapoint.
    Is an instance of a field with a value for a record.."""

    def __init__(
        self,
        field_id: str,
        raw_value: typing.Union[str, int],
        study: "CastorStudy",
        filled_in: str,
    ) -> None:
        """Creates a CastorField."""
        self.field_id = field_id
        self.raw_value = raw_value
        self.instance_of = self.find_field(study)
        if self.instance_of is None:
            raise CastorException(
                "The field that this is an instance of does not exist in the study!"
            )
        self.form_instance = None
        self.filled_in = (
            None
            if filled_in == ""
            else datetime.strptime(filled_in, "%Y-%m-%d %H:%M:%S")
        )
        # Is missing
        self.value = self.__interpret(study)

    # Helpers
    def find_field(self, study: "CastorStudy") -> "CastorField":
        """Returns a single field in the study on id."""
        return study.get_single_field(self.field_id)

    def __interpret(self, study: "CastorStudy"):
        """Transform the raw value into analysable data."""
        if self.instance_of.field_type in ["checkbox", "dropdown", "radio"]:
            interpreted_value = self.__interpret_optiongroup(study)
        elif self.instance_of.field_type in [
            "numeric",
            "slider",
            "randomization",
        ]:
            interpreted_value = self.__interpret_numeric()
        elif self.instance_of.field_type in ["year"]:
            interpreted_value = self.__interpret_year()
        elif self.instance_of.field_type in [
            "string",
            "textarea",
            "upload",
            "calculation",
        ]:
            interpreted_value = self.raw_value
        elif self.instance_of.field_type in ["datetime"]:
            interpreted_value = self.__interpret_datetime(
                study.configuration["datetime"]
            )
        elif self.instance_of.field_type in ["date"]:
            interpreted_value = self.__interpret_date(study.configuration["date"])
        elif self.instance_of.field_type in ["time"]:
            interpreted_value = self.__interpret_time(study.configuration["time"])
        elif self.instance_of.field_type in ["numberdate"]:
            interpreted_value = self.__interpret_numberdate(study.configuration["date"])
        elif self.instance_of.field_type in ["grid"]:
            interpreted_value = self.__interpret_grid(study)
        else:
            interpreted_value = "Error"
        return interpreted_value

    def __interpret_time(self, time_format: str):
        """Interprets time missing data while handling user missings."""
        if self.raw_value == "":
            new_value = ""
        elif "Missing" in self.raw_value:
            if "measurement failed" in self.raw_value:
                new_value = "-95"
            elif "not applicable" in self.raw_value:
                new_value = "-96"
            elif "not asked" in self.raw_value:
                new_value = "-97"
            elif "asked but unknown" in self.raw_value:
                new_value = "-98"
            elif "not done" in self.raw_value:
                new_value = "-99"
            else:
                new_value = "Missing value not recognized"
        else:
            new_value = (
                datetime.strptime(self.raw_value, "%H:%M").time().strftime(time_format)
            )
        return new_value

    def __interpret_datetime(self, datetime_format: str):
        """Interprets date and datetime data while handling user missings."""
        if self.raw_value == "":
            new_value = np.nan
        elif "Missing" in self.raw_value:
            if "measurement failed" in self.raw_value:
                new_value = pd.Period(year=2995, month=1, day=1, freq="s").strftime(
                    datetime_format
                )
            elif "not applicable" in self.raw_value:
                new_value = pd.Period(year=2996, month=1, day=1, freq="s").strftime(
                    datetime_format
                )
            elif "not asked" in self.raw_value:
                new_value = pd.Period(year=2997, month=1, day=1, freq="s").strftime(
                    datetime_format
                )
            elif "asked but unknown" in self.raw_value:
                new_value = pd.Period(year=2998, month=1, day=1, freq="s").strftime(
                    datetime_format
                )
            elif "not done" in self.raw_value:
                new_value = pd.Period(year=2999, month=1, day=1, freq="s").strftime(
                    datetime_format
                )
            else:
                new_value = "Missing value not recognized"
        else:
            try:
                new_value = pd.Period(
                    datetime.strptime(self.raw_value, "%d-%m-%Y;%H:%M"), freq="s"
                ).strftime(datetime_format)
            except ValueError:
                new_value = pd.Period(
                    datetime.strptime(self.raw_value, "%d-%m-%Y"), freq="s"
                ).strftime(datetime_format)

        return new_value

    def __interpret_date(self, date_format: str):
        """Interprets date and datetime data while handling user missings."""
        if self.raw_value == "":
            new_value = np.nan
        elif "Missing" in self.raw_value:
            if "measurement failed" in self.raw_value:
                new_value = pd.Period(year=2995, month=1, day=1, freq="D").strftime(
                    date_format
                )
            elif "not applicable" in self.raw_value:
                new_value = pd.Period(year=2996, month=1, day=1, freq="D").strftime(
                    date_format
                )
            elif "not asked" in self.raw_value:
                new_value = pd.Period(year=2997, month=1, day=1, freq="D").strftime(
                    date_format
                )
            elif "asked but unknown" in self.raw_value:
                new_value = pd.Period(year=2998, month=1, day=1, freq="D").strftime(
                    date_format
                )
            elif "not done" in self.raw_value:
                new_value = pd.Period(year=2999, month=1, day=1, freq="D").strftime(
                    date_format
                )
            else:
                new_value = "Missing value not recognized"
        else:
            try:
                new_value = pd.Period(
                    datetime.strptime(self.raw_value, "%d-%m-%Y"), freq="D"
                ).strftime(date_format)
            except ValueError:
                new_value = pd.Period(
                    datetime.strptime(self.raw_value, "%d-%m-%Y;%H:%M"), freq="s"
                ).strftime("%d-%m-%Y;%H:%M")

        return new_value

    def __interpret_optiongroup(self, study: "CastorStudy"):
        """Interprets optiongroup data while handling user missings."""
        if self.raw_value == "":
            new_value = ""
        elif "Missing" in self.raw_value:
            if "measurement failed" in self.raw_value:
                new_value = "measurement failed"
            elif "not applicable" in self.raw_value:
                new_value = "not applicable"
            elif "not asked" in self.raw_value:
                new_value = "not asked"
            elif "asked but unknown" in self.raw_value:
                new_value = "asked but unknown"
            elif "not done" in self.raw_value:
                new_value = "not done"
            else:
                new_value = "Missing value not recognized"
        else:
            new_value = self.__interpret_optiongroup_helper(study)
        return new_value

    def __interpret_optiongroup_helper(self, study):
        """Interprets values in an optiongroup field."""
        # Get the optiongroup for this data point
        optiongroup = self.instance_of.field_option_group
        # Retrieve the options
        study_optiongroup = study.get_single_optiongroup(optiongroup)
        if study_optiongroup is None:
            raise CastorException(
                "Optiongroup not found. Is id correct and are optiongroups loaded?"
            )
        # Get options
        options = study_optiongroup["options"]
        # Transform options into dict value: name
        link = {item["value"]: item["name"] for item in options}
        # Get values, split by ; for checklists
        value_list = self.raw_value.split(";")
        # Values to names
        if value_list == [""]:
            new_values = [""]
        elif study.pass_keyerrors:
            new_values = [link.get(value, value) for value in value_list]
        else:
            try:
                new_values = [link[value] for value in value_list]
            except KeyError as error:
                raise CastorException(
                    f"Optional value mapping failed for optiongroup: {study_optiongroup}"
                    f"Key `{self.raw_value}` not present in the keys of the optiongroup"
                    f"of field: {self.field_id} ({self.instance_of.field_name})"
                ) from error
        # Return a string, for multiple answers separate them with |
        new_value = "|".join(new_values)
        return new_value

    def __interpret_numeric(self):
        """Interprets numeric data while handling user missings."""
        if self.raw_value == "":
            new_value = np.nan
        elif "Missing" in self.raw_value:
            if "measurement failed" in self.raw_value:
                new_value = -95
            elif "not applicable" in self.raw_value:
                new_value = -96
            elif "not asked" in self.raw_value:
                new_value = -97
            elif "asked but unknown" in self.raw_value:
                new_value = -98
            elif "not done" in self.raw_value:
                new_value = -99
            else:
                new_value = "Missing value not recognized"
        else:
            new_value = float(self.raw_value)
        return new_value

    def __interpret_year(self):
        """Interprets year data while handling user missings."""
        if self.raw_value == "":
            new_value = np.nan
        elif "Missing" in self.raw_value:
            if "measurement failed" in self.raw_value:
                new_value = -95
            elif "not applicable" in self.raw_value:
                new_value = -96
            elif "not asked" in self.raw_value:
                new_value = -97
            elif "asked but unknown" in self.raw_value:
                new_value = -98
            elif "not done" in self.raw_value:
                new_value = -99
            else:
                new_value = "Missing value not recognized"
        else:
            new_value = int(self.raw_value)
        return new_value

    def __interpret_numberdate(self, date_format: str):
        """Interprets numberdate data while handling user missings."""
        if self.raw_value == "":
            new_value = [
                np.nan,
                np.nan,
            ]
        elif "Missing" in self.raw_value:
            if "measurement failed" in self.raw_value:
                new_value = [
                    -95,
                    pd.Period(year=2995, month=1, day=1, freq="D").strftime(
                        date_format
                    ),
                ]
            elif "not applicable" in self.raw_value:
                new_value = [
                    -96,
                    pd.Period(year=2996, month=1, day=1, freq="D").strftime(
                        date_format
                    ),
                ]
            elif "not asked" in self.raw_value:
                new_value = [
                    -97,
                    pd.Period(year=2997, month=1, day=1, freq="D").strftime(
                        date_format
                    ),
                ]
            elif "asked but unknown" in self.raw_value:
                new_value = [
                    -98,
                    pd.Period(year=2998, month=1, day=1, freq="D").strftime(
                        date_format
                    ),
                ]
            elif "not done" in self.raw_value:
                new_value = [
                    -99,
                    pd.Period(year=2999, month=1, day=1, freq="D").strftime(
                        date_format
                    ),
                ]
            else:
                new_value = [
                    "Missing value not recognized",
                    "Missing value not recognized",
                ]
        else:
            # Get number and date from the string
            number, date = self.raw_value.split(";")
            # Combine
            if number == "":
                number = np.nan
            if date == "":
                date = np.nan
            new_value = [
                float(number),
                pd.Period(datetime.strptime(date, "%d-%m-%Y"), freq="D").strftime(
                    date_format
                ),
            ]
        return new_value

    import re
    def __interpret_grid(self, study):
        """Interprets values in a grid field."""
        if self.raw_value == "" or self.instance_of.field_summary_template == "":
            new_value = np.nan
        else:
            #new_value = np.nan
            try:
                cols_interpreted = []
                grid_template = json.loads(self.instance_of.field_summary_template)

                try:
                    grid_rows = list(json.loads(self.raw_value).values())
                except json.decoder.JSONDecodeError:
                    # attempt to fix broken json
                    #print("Attempting to fix broken JSON.")
                    # TODO: fix manually for now
                    print(f"Broken JSON: {self.raw_value}")
                    
                    # fixed_json = (
                    #     re.sub(
                    #         r'(?<=: )"{2,}(.*?){2,}(?=[:,}])', 
                    #         r'"\1"', 
                    #         self.raw_value
                    #         .replace('\\', '')
                    #         .replace('""', '"')
                    #     ).rstrip('"')
                    # )
                    # grid_rows = json.loads(fixed_json).values()

                raw_grid_df = pd.DataFrame(grid_rows)

                if raw_grid_df.shape[0] != raw_grid_df.shape[1]:
                    # if field types are for columns, keep format
                    if len(grid_template['fieldTypes']) == raw_grid_df.shape[1]:
                        row_names = grid_template['rowNames']
                        col_names = grid_template['columnNames']
                    # otherwise, if for rows, transpose
                    else:
                        raw_grid_df = raw_grid_df.T
                        row_names = grid_template['columnNames']
                        col_names = grid_template['rowNames']
                else:
                    # if rows and columns are equivalent in length, check which of
                    # rows and columns are equivalent to find what matches with field types
                    col_check = [col_name.split(' ')[0] for col_name in grid_template['columnNames']]
                    row_check = [row_name.split(' ')[0] for row_name in grid_template['rowNames']]
                    if all(x == col_check[0] for x in col_check):
                        raw_grid_df = raw_grid_df.T
                        row_names = grid_template['columnNames']
                        col_names = grid_template['rowNames']
                    elif all(x == row_check[0] for x in row_check):
                        row_names = grid_template['rowNames']
                        col_names = grid_template['columnNames']

                # get the interpreted value of the grid cells by creating a
                # CastorGridCell instance for each cell
                for col_num, col in enumerate(raw_grid_df.columns):
                    col_data = raw_grid_df[col].tolist()

                    field_type = grid_template['fieldTypes'][col_num]
                    option_group = grid_template['optionLists'][col_num]

                    my_instance_of = CastorField(
                        self.instance_of.field_name + " - grid object",
                        None,
                        field_type,
                        None,
                        None,
                        option_group,
                        None
                    )

                    cols_interpreted.append(
                        [interpret(study, my_instance_of, cell) for cell in col_data]
                    )

                grid_df = pd.DataFrame(cols_interpreted).T
                grid_df.columns = [col.strip() for col in col_names]
                grid_df.index = [row.strip() for row in row_names]

                new_value = grid_df
            except:
                new_value = "Error"

        return new_value

    # Standard Operators
    def __eq__(self, other: typing.Any) -> typing.Union[bool, type(NotImplemented)]:
        if not isinstance(other, CastorDataPoint):
            return NotImplemented
        return (
            (self.field_id == other.field_id)
            and (self.form_instance == other.form_instance)
            and (self.form_instance.record == other.form_instance.record)
        )

    def __repr__(self) -> str:
        return (
            self.form_instance.record.record_id
            + " - "
            + self.form_instance.instance_of.form_name
            + " - "
            + self.instance_of.field_name
        )


def interpret(study: "CastorStudy", instance_of, raw_value):
    """Transform the raw value into analysable data."""
    if instance_of.field_type in ["checkbox", "dropdown", "radio"]:
        interpreted_value = interpret_optiongroup(study, instance_of, raw_value)
    elif instance_of.field_type in [
        "numeric",
        "slider",
        "randomization",
    ]:
        interpreted_value = interpret_numeric(raw_value)
    elif instance_of.field_type in ["year"]:
        interpreted_value = interpret_year(raw_value)
    elif instance_of.field_type in [
        "string",
        "textarea",
        "upload",
        "calculation",
    ]:
        interpreted_value = raw_value
    elif instance_of.field_type in ["datetime"]:
        interpreted_value = interpret_datetime(
            study.configuration["datetime"], raw_value
        )
    elif instance_of.field_type in ["date"]:
        interpreted_value = interpret_date(study.configuration["date"], raw_value)
    elif instance_of.field_type in ["time"]:
        interpreted_value = interpret_time(study.configuration["time"], raw_value)
    elif instance_of.field_type in ["numberdate"]:
        interpreted_value = interpret_numberdate(study.configuration["date"], raw_value)
    else:
        interpreted_value = "Error"
    return interpreted_value

def interpret_time(time_format: str, raw_value):
    """Interprets time missing data while handling user missings."""
    if raw_value == "":
        new_value = ""
    elif "Missing" in raw_value:
        if "measurement failed" in raw_value:
            new_value = "-95"
        elif "not applicable" in raw_value:
            new_value = "-96"
        elif "not asked" in raw_value:
            new_value = "-97"
        elif "asked but unknown" in raw_value:
            new_value = "-98"
        elif "not done" in raw_value:
            new_value = "-99"
        else:
            new_value = "Missing value not recognized"
    else:
        new_value = (
            datetime.strptime(raw_value, "%H:%M").time().strftime(time_format)
        )
    return new_value

def interpret_datetime(datetime_format: str, raw_value):
    """Interprets date and datetime data while handling user missings."""
    if raw_value == "":
        new_value = np.nan
    elif "Missing" in raw_value:
        if "measurement failed" in raw_value:
            new_value = pd.Period(year=2995, month=1, day=1, freq="s").strftime(
                datetime_format
            )
        elif "not applicable" in raw_value:
            new_value = pd.Period(year=2996, month=1, day=1, freq="s").strftime(
                datetime_format
            )
        elif "not asked" in raw_value:
            new_value = pd.Period(year=2997, month=1, day=1, freq="s").strftime(
                datetime_format
            )
        elif "asked but unknown" in raw_value:
            new_value = pd.Period(year=2998, month=1, day=1, freq="s").strftime(
                datetime_format
            )
        elif "not done" in raw_value:
            new_value = pd.Period(year=2999, month=1, day=1, freq="s").strftime(
                datetime_format
            )
        else:
            new_value = "Missing value not recognized"
    else:
        try:
            new_value = pd.Period(
                datetime.strptime(raw_value, "%d-%m-%Y;%H:%M"), freq="s"
            ).strftime(datetime_format)
        except ValueError:
            new_value = pd.Period(
                datetime.strptime(raw_value, "%d-%m-%Y"), freq="s"
            ).strftime(datetime_format)

    return new_value

def interpret_date(date_format: str, raw_value):
    """Interprets date and datetime data while handling user missings."""
    if raw_value == "":
        new_value = np.nan
    elif "Missing" in raw_value:
        if "measurement failed" in raw_value:
            new_value = pd.Period(year=2995, month=1, day=1, freq="D").strftime(
                date_format
            )
        elif "not applicable" in raw_value:
            new_value = pd.Period(year=2996, month=1, day=1, freq="D").strftime(
                date_format
            )
        elif "not asked" in raw_value:
            new_value = pd.Period(year=2997, month=1, day=1, freq="D").strftime(
                date_format
            )
        elif "asked but unknown" in raw_value:
            new_value = pd.Period(year=2998, month=1, day=1, freq="D").strftime(
                date_format
            )
        elif "not done" in raw_value:
            new_value = pd.Period(year=2999, month=1, day=1, freq="D").strftime(
                date_format
            )
        else:
            new_value = "Missing value not recognized"
    else:
        try:
            new_value = pd.Period(
                datetime.strptime(raw_value, "%d-%m-%Y"), freq="D"
            ).strftime(date_format)
        except ValueError:
            new_value = pd.Period(
                datetime.strptime(raw_value, "%d-%m-%Y;%H:%M"), freq="s"
            ).strftime("%d-%m-%Y;%H:%M")

    return new_value

def interpret_optiongroup(study: "CastorStudy", instance_of, raw_value):
    """Interprets optiongroup data while handling user missings."""
    if raw_value == "":
        new_value = ""
    elif "Missing" in raw_value:
        if "measurement failed" in raw_value:
            new_value = "measurement failed"
        elif "not applicable" in raw_value:
            new_value = "not applicable"
        elif "not asked" in raw_value:
            new_value = "not asked"
        elif "asked but unknown" in raw_value:
            new_value = "asked but unknown"
        elif "not done" in raw_value:
            new_value = "not done"
        else:
            new_value = "Missing value not recognized"
    else:
        new_value = interpret_optiongroup_helper(study, instance_of, raw_value)
    return new_value

def interpret_optiongroup_helper(study, instance_of, raw_value):
    """Interprets values in an optiongroup field."""
    # Get the optiongroup for this data point
    optiongroup = instance_of.field_option_group
    # Retrieve the options
    study_optiongroup = study.get_single_optiongroup(optiongroup)
    if study_optiongroup is None:
        raise CastorException(
            "Optiongroup not found. Is id correct and are optiongroups loaded?"
        )
    # Get options
    options = study_optiongroup["options"]
    # Transform options into dict value: name
    link = {item["value"]: item["name"] for item in options}
    # Get values, split by ; for checklists
    value_list = raw_value.split(";")
    # Values to names
    if value_list == [""]:
        new_values = [""]
    elif study.pass_keyerrors:
        new_values = [link.get(value, value) for value in value_list]
    else:
        try:
            new_values = [link[value] for value in value_list]
        except KeyError as error:
            raise CastorException(
                f"Optional value mapping failed for optiongroup: {study_optiongroup}"
                f"Key `{raw_value}` not present in the keys of the optiongroup"
                #f"of field: {self.field_id} ({instance_of.field_name})"
            ) from error
    # Return a string, for multiple answers separate them with |
    new_value = "|".join(new_values)
    return new_value

def interpret_numeric(raw_value):
    """Interprets numeric data while handling user missings."""
    if raw_value == "":
        new_value = np.nan
    elif "Missing" in raw_value:
        if "measurement failed" in raw_value:
            new_value = -95
        elif "not applicable" in raw_value:
            new_value = -96
        elif "not asked" in raw_value:
            new_value = -97
        elif "asked but unknown" in raw_value:
            new_value = -98
        elif "not done" in raw_value:
            new_value = -99
        else:
            new_value = "Missing value not recognized"
    else:
        new_value = float(raw_value)
    return new_value

def interpret_year(raw_value):
    """Interprets year data while handling user missings."""
    if raw_value == "":
        new_value = np.nan
    elif "Missing" in raw_value:
        if "measurement failed" in raw_value:
            new_value = -95
        elif "not applicable" in raw_value:
            new_value = -96
        elif "not asked" in raw_value:
            new_value = -97
        elif "asked but unknown" in raw_value:
            new_value = -98
        elif "not done" in raw_value:
            new_value = -99
        else:
            new_value = "Missing value not recognized"
    else:
        new_value = int(raw_value)
    return new_value

def interpret_numberdate(date_format: str, raw_value):
    """Interprets numberdate data while handling user missings."""
    if raw_value == "":
        new_value = [
            np.nan,
            np.nan,
        ]
    elif "Missing" in raw_value:
        if "measurement failed" in raw_value:
            new_value = [
                -95,
                pd.Period(year=2995, month=1, day=1, freq="D").strftime(
                    date_format
                ),
            ]
        elif "not applicable" in raw_value:
            new_value = [
                -96,
                pd.Period(year=2996, month=1, day=1, freq="D").strftime(
                    date_format
                ),
            ]
        elif "not asked" in raw_value:
            new_value = [
                -97,
                pd.Period(year=2997, month=1, day=1, freq="D").strftime(
                    date_format
                ),
            ]
        elif "asked but unknown" in raw_value:
            new_value = [
                -98,
                pd.Period(year=2998, month=1, day=1, freq="D").strftime(
                    date_format
                ),
            ]
        elif "not done" in raw_value:
            new_value = [
                -99,
                pd.Period(year=2999, month=1, day=1, freq="D").strftime(
                    date_format
                ),
            ]
        else:
            new_value = [
                "Missing value not recognized",
                "Missing value not recognized",
            ]
    else:
        # Get number and date from the string
        number, date = raw_value.split(";")
        # Combine
        if number == "":
            number = np.nan
        if date == "":
            date = np.nan
        new_value = [
            float(number),
            pd.Period(datetime.strptime(date, "%d-%m-%Y"), freq="D").strftime(
                date_format
            ),
        ]
    return new_value