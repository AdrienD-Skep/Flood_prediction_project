# original code from :  https://github.com/philiprt/GeslaDataset
import pandas as pd
import xarray as xr
from datetime import date, datetime


class GeslaDataset:
    """A class for loading data from GESLA text files into convenient in-memory
    data objects. By default, single file requests are loaded into
    `pandas.DataFrame` objects, which are similar to in-memory spreadsheets.
    Multifile requests are loaded into `xarray.Dataset` objects, which are
    similar to in-memory NetCDF files."""

    def __init__(self, meta_file, data_path):
        """Initialize loading data from a GESLA database.

        Args:
            meta_file (string): path to the metadata file in .csv format.
            data_path (string): path to the directory containing GESLA data
                files.
        """
        self.meta = pd.read_csv(meta_file)
        self.meta.columns = [
            c.replace(" ", "_")
            .replace("(", "")
            .replace(")", "")
            .replace("/", "_")
            .lower()
            for c in self.meta.columns
        ]
        self.meta.loc[:, "start_date_time"] = [
            pd.to_datetime(d) for d in self.meta.loc[:, "start_date_time"]
        ]
        self.meta.loc[:, "end_date_time"] = [
            pd.to_datetime(d) for d in self.meta.loc[:, "end_date_time"]
        ]
        self.meta.rename(columns={"file_name": "filename"}, inplace=True)
        self.data_path = data_path

    def file_to_pandas(self, filename, return_meta=True):
        """Read a GESLA data file into a pandas.DataFrame object. Metadata is
        returned as a pandas.Series object.

        Args:
            filename (string): name of the GESLA data file. Do not prepend path.
            return_meta (bool, optional): determines if metadata is returned as
                a second function output. Defaults to True.

        Returns:
            pandas.DataFrame: sea-level values and flags with datetime index.
            pandas.Series: record metadata. This return can be excluded by
                setting return_meta=False.
        """
        data = pd.read_csv(
            self.data_path + filename,
            skiprows=41,
            names=["date", "time", "sea_level", "qc_flag", "use_flag"],
            sep=r"\s+",
            dtype={
                'date': 'str',
                'time': 'str',
                'sea_level': 'float32',  # Adjust based on precision needs
                'qc_flag': 'int',   # If limited unique values
                'use_flag': 'int'
            }
        )
        # Combine 'date' and 'time' columns into a single datetime column
        data['datetime'] = pd.to_datetime(data['date'] + ' ' + data['time'])

        # Set the 'datetime' column as the index
        data.set_index('datetime', inplace=True)

        # Optional: Drop the now-redundant 'date' and 'time' columns
        data.drop(columns=['date', 'time'], inplace=True)
        duplicates = data.index.duplicated()
        if duplicates.sum() > 0:
            data = data.loc[~duplicates]
            # warnings.warn(
            #     "Duplicate timestamps in file " + filename + " were removed.",
            # )
        if return_meta:
            meta = self.meta.loc[self.meta.filename == filename].iloc[0]
            return data, meta
        else:
            return data

    def files_to_xarray(self, filenames):
        """Read a list of GESLA filenames into a xarray.Dataset object. The
        dataset includes variables containing metadata for each record.

        Args:
            filenames (list): list of filename strings.

        Returns:
            xarray.Dataset: data, flags, and metadata for each record.
        """
        data = xr.concat(
            [self.file_to_pandas(f, return_meta=False).to_xarray() for f in filenames],
            dim="station",
        )

        idx = [s.Index for s in self.meta.itertuples() if s.filename in filenames]
        meta = self.meta.loc[idx]
        meta.index = range(meta.index.size)
        meta.index.name = "station"
        data = data.assign({c: meta[c] for c in meta.columns})

        return data

    def load_N_closest(self, lat, lon, N=1, force_xarray=False, start_date=None, end_date=None, b_filter_quality = False, return_only_filename_list = False):
        """Load the N closest GESLA records to a lat/lon location into a
        xarray.Dataset object. The dataset includes variables containing
        metadata for each record.

        Args:
            lat (float): latitude on the interval [-90, 90]
            lon (float): longitude on the interval [-180, 180]
            N (int, optional): number of locations to load. Defaults to 1.
            force_xarray (bool, optional): if N=1, the default behavior is to
                return a pandas.DataFrame object containing data/flags and a
                pandas.Series object containing metadata. Set this argument to
                True to return a xarray Dataset even if N=1. Defaults to False.
            start_date (datetime, optional): Start date for filtering records.
            end_date (datetime, optional): End date for filtering records.
            return_only_filename_list (bool, optional) : Set this argument to
                True to return a list of filenames

        Returns:
            xarray.Dataset: data, flags, and metadata for each record.
        """
        N = int(N)
        if N <= 0:
            raise Exception("Must specify N > 0")

        # Ensure start_date and end_date are valid datetime objects
        if start_date and not isinstance(end_date, (datetime, date)):
            raise ValueError("start_date must be a datetime object")
        if end_date and not isinstance(end_date, (datetime, date)):
            raise ValueError("end_date must be a datetime object")

        # Filter self.meta based on the date range
        filtered_meta = self.meta
        if start_date is not None:
            filtered_meta = filtered_meta[filtered_meta['start_date_time'] <= start_date]
        if end_date is not None:
            filtered_meta = filtered_meta[filtered_meta['end_date_time'] >= end_date]

        if (b_filter_quality): 
            filtered_meta = filtered_meta[filtered_meta['overall_record_quality'] == "No obvious issues"]
        # Calculate distances and get indices of the N closest records
        d = (filtered_meta.longitude - lon) ** 2 + (filtered_meta.latitude - lat) ** 2
        idx = d.sort_values().iloc[:N].index
        meta = filtered_meta.loc[idx].reindex(idx)
        if return_only_filename_list :
            return meta.filename.tolist()

        if (N > 1) or force_xarray:
            concatenated_ds = self.files_to_xarray(meta.filename.tolist())
            if start_date is not None and end_date is not None :
                concatenated_ds = concatenated_ds.sel(datetime=slice(start_date, end_date))
            return concatenated_ds

        else:
            data, meta = self.file_to_pandas(meta.filename.values[0])
            if start_date is not None:
                data = data[data.index >= start_date]
            if end_date is not None:
                data = data[data.index <= end_date]
            return data, meta

    def load_lat_lon_range(
        self,
        south_lat=-90,
        north_lat=90,
        west_lon=-180,
        east_lon=180,
        force_xarray=False,
        start_date=None, 
        end_date=None,
        b_filter_quality = False
    ):
        """Load GESLA records within a rectangular lat/lon range into a xarray.
        Dataset object.

        Args:
            south_lat (float, optional): southern extent of the range. Defaults
                to -90.
            north_lat (float, optional): northern extent of the range. Defaults
                to 90.
            west_lon (float, optional): western extent of the range. Defaults
                to -180.
            east_lon (float, optional): eastern extent of the range. Defaults
                to 180.
            force_xarray (bool, optional): if there is only one record in the
                lat/lon range, the default behavior is to return a
                pandas.DataFrame object containing data/flags and a
                pandas.Series object containing metadata. Set this argument to
                True to return a xarray.Dataset even if only one record is
                selected. Defaults to False.

        Returns:
            xarray.Dataset: data, flags, and metadata for each record.
        """

         # Filter self.meta based on the date range
        filtered_meta = self.meta
        if start_date is not None:
            filtered_meta = filtered_meta[filtered_meta['start_date_time'] <= start_date]
        if end_date is not None:
            filtered_meta = filtered_meta[filtered_meta['end_date_time'] >= end_date]

        if (b_filter_quality): 
            filtered_meta = filtered_meta[filtered_meta['overall_record_quality'] == "No obvious issues"]


        if west_lon > east_lon:
            lon_bool = (filtered_meta.longitude >= west_lon) | (
                filtered_meta.longitude <= east_lon
            )
        else:
            lon_bool = (filtered_meta.longitude >= west_lon) & (
                filtered_meta.longitude <= east_lon
            )
        lat_bool = (filtered_meta.latitude >= south_lat) & (filtered_meta.latitude <= north_lat)
        meta = filtered_meta.loc[lon_bool & lat_bool]

        if (meta.index.size > 1) or force_xarray:
            return self.files_to_xarray(meta.filename.tolist())

        else:
            data, meta = self.file_to_pandas(meta.filename.values[0])
            return data, meta