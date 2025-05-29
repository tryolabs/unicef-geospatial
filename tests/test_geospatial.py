"""Test cases for geospatial operations."""

from unittest.mock import Mock, patch

import pytest
from ee.feature import Feature
from ee.featurecollection import FeatureCollection
from ee.image import Image
from geospatial.demographic import (
    get_country_code,
    get_zone_of_area,
    standarize_country_name,
)
from geospatial.earth_engine import (
    create_bucket,
    create_ee_asset_path,
    get_dataset_metadata,
    upload_blob,
    upload_bucket_to_ee,
    upload_directory,
    upload_to_ee_from_gcs,
)
from geospatial.geo_operations import (
    build_map,
    filter_image_by_threshold,
    get_dataset_image_and_metadata,
    intersect_binary_images,
    intersect_feature,
    intersect_feature_collections,
    mask_image,
    merge_feature_collections,
    reduce_image,
    union_binary_images,
)
from geospatial.hazards_metadata import get_ccri_metadata
from utils.types import ALL_DATASETS


class TestGetMetadata:
    @patch("geospatial.geo_operations.get_dataset_metadata")
    @patch("geospatial.geo_operations.save_ee_object")
    @patch("geospatial.geo_operations.ImageCollection")
    @patch("geospatial.geo_operations.Image")
    def test_get_dataset_with_mosaic(
        self, mock_image, mock_image_collection, mock_save, mock_get_metadata
    ):
        """Test getting dataset with mosaic=True."""
        mock_metadata = Mock()
        mock_metadata.asset_id = "test/asset"
        mock_metadata.mosaic = True
        mock_metadata.image_filename = "test_image.json"
        mock_metadata.model_dump.return_value = {
            "asset_id": "test/asset",
            "image_filename": "test_image.json",
            "description": "Test dataset",
            "threshold": 0.5,
        }
        mock_get_metadata.return_value = mock_metadata

        mock_collection = Mock()
        mock_mosaic = Mock()
        mock_collection.mosaic.return_value = mock_mosaic
        mock_image_collection.return_value = mock_collection

        result = get_dataset_image_and_metadata(ALL_DATASETS.RIVER_FLOOD, "/tmp")

        mock_get_metadata.assert_called_once_with(ALL_DATASETS.RIVER_FLOOD)
        mock_image_collection.assert_called_once_with("test/asset")
        mock_collection.mosaic.assert_called_once()
        mock_save.assert_called_once()

        assert "asset_id" in result
        assert "image_filename" in result
        assert "description" in result
        assert "input_arguments" in result
        assert result["input_arguments"]["dataset"] == ALL_DATASETS.RIVER_FLOOD

    @patch("geospatial.geo_operations.get_dataset_metadata")
    @patch("geospatial.geo_operations.save_ee_object")
    @patch("geospatial.geo_operations.Image")
    def test_get_dataset_without_mosaic(self, mock_image, mock_save, mock_get_metadata):
        """Test getting dataset with mosaic=False."""
        mock_metadata = Mock()
        mock_metadata.asset_id = "test/asset"
        mock_metadata.mosaic = False
        mock_metadata.image_filename = "test_image.json"
        mock_metadata.model_dump.return_value = {
            "asset_id": "test/asset",
            "image_filename": "test_image.json",
            "description": "Test dataset",
        }
        mock_get_metadata.return_value = mock_metadata

        mock_ee_image = Mock()
        mock_image.return_value = mock_ee_image

        result = get_dataset_image_and_metadata(ALL_DATASETS.FIRE, "/tmp")

        mock_get_metadata.assert_called_once_with(ALL_DATASETS.FIRE)
        mock_image.assert_called_once_with("test/asset")
        mock_save.assert_called_once()
        assert "input_arguments" in result

    @patch("geospatial.geo_operations.get_dataset_metadata")
    @patch("geospatial.geo_operations.save_ee_object")
    @patch("geospatial.geo_operations.Image")
    def test_get_agricultural_drought_dataset(
        self, mock_image, mock_save, mock_get_metadata
    ):
        """Test getting agricultural drought dataset with special handling."""
        mock_metadata = Mock()
        mock_metadata.asset_id = "test/asset"
        mock_metadata.mosaic = False
        mock_metadata.image_filename = "drought_image.json"
        mock_metadata.model_dump.return_value = {
            "asset_id": "test/asset",
            "image_filename": "drought_image.json",
            "description": "Drought dataset",
        }
        mock_get_metadata.return_value = mock_metadata

        mock_ee_image = Mock()
        mock_updated_image = Mock()
        mock_ee_image.lte.return_value = mock_updated_image
        mock_ee_image.updateMask.return_value = mock_updated_image
        mock_image.return_value = mock_ee_image

        result = get_dataset_image_and_metadata(
            ALL_DATASETS.AGRICULTURAL_DROUGHT, "/tmp"
        )

        mock_ee_image.lte.assert_called_once_with(100)
        mock_ee_image.updateMask.assert_called_once()
        mock_save.assert_called_once()
        assert "input_arguments" in result

    @patch("geospatial.hazards_metadata.load_index_from_storage")
    @patch("geospatial.hazards_metadata.StorageContext")
    @patch("geospatial.hazards_metadata.VectorIndexRetriever")
    def test_get_ccri_metadata(
        self, mock_retriever_class, mock_storage_context, mock_load_index
    ):
        mock_storage_context.from_defaults.return_value = Mock()
        mock_load_index.return_value = Mock()
        mock_retriever = Mock()
        mock_retriever_class.return_value = mock_retriever

        mock_response_1 = Mock()
        mock_response_1.text = "CCRI documentation part 1"
        mock_response_2 = Mock()
        mock_response_2.text = "CCRI documentation part 2"
        mock_retriever.retrieve.return_value = [mock_response_1, mock_response_2]

        result = get_ccri_metadata("climate risk methodology")

        mock_storage_context.from_defaults.assert_called_once()
        assert result == "CCRI documentation part 1\nCCRI documentation part 2"


class TestImageOperations:

    @patch("geospatial.geo_operations.load_vector_data")
    @patch("geospatial.geo_operations.save_ee_object")
    def test_mask_image_success(self, mock_save, mock_load):
        """Test successful image masking."""
        mock_image = Mock(spec=Image)
        mock_mask = Mock(spec=Image)
        mock_masked_image = Mock()
        mock_image.updateMask.return_value = mock_masked_image

        mock_load.side_effect = [mock_image, mock_mask]

        result = mask_image("image.json", "mask.json", "/tmp")

        assert mock_load.call_count == 2
        mock_image.updateMask.assert_called_once_with(mock_mask)
        mock_save.assert_called_once()
        assert result["image_filename"] == "image_masked.json"
        assert "input_arguments" in result

    @patch("geospatial.geo_operations.load_vector_data")
    def test_mask_image_invalid_image_type(self, mock_load):
        """Test mask_image with invalid image type."""
        mock_load.side_effect = [Mock(), Mock(spec=Image)]

        with pytest.raises(TypeError, match="Expected an Earth Engine Image object"):
            mask_image("image.json", "mask.json", "/tmp")

    @patch("geospatial.geo_operations.load_vector_data")
    @patch("geospatial.geo_operations.save_ee_object")
    @patch("geospatial.geo_operations.ee.Number")
    def test_filter_image_positive_threshold(self, mock_number, mock_save, mock_load):
        """Test filtering image with positive threshold."""
        mock_image = Mock(spec=Image)
        mock_filtered = Mock()
        mock_image.gt.return_value = mock_filtered
        mock_load.return_value = mock_image
        mock_number.return_value = Mock()

        result = filter_image_by_threshold("image.json", 35.0, "/tmp")

        mock_load.assert_called_once()
        mock_number.assert_called_once_with(35.0)
        mock_image.gt.assert_called_once()
        mock_save.assert_called_once()
        assert result["image_filename"] == "image_filtered.json"
        assert result["input_arguments"]["threshold"] == 35.0

    @patch("geospatial.geo_operations.load_vector_data")
    @patch("geospatial.geo_operations.save_ee_object")
    @patch("geospatial.geo_operations.ee.Number")
    def test_filter_image_negative_threshold(self, mock_number, mock_save, mock_load):
        """Test filtering image with negative threshold."""
        mock_image = Mock(spec=Image)
        mock_filtered = Mock()
        mock_image.lt.return_value = mock_filtered
        mock_load.return_value = mock_image
        mock_number.return_value = Mock()

        result = filter_image_by_threshold("image.json", -1.0, "/tmp")

        mock_image.lt.assert_called_once()
        assert result["input_arguments"]["threshold"] == -1.0

    @patch("geospatial.geo_operations.load_vector_data")
    def test_filter_image_invalid_type(self, mock_load):
        """Test filter_image_by_threshold with invalid image type."""
        mock_load.return_value = Mock()

        with pytest.raises(TypeError, match="Expected an Earth Engine Image object"):
            filter_image_by_threshold("image.json", 35.0, "/tmp")

    @patch("geospatial.geo_operations.load_vector_data")
    @patch("geospatial.geo_operations.save_ee_object")
    def test_union_binary_images(self, mock_save, mock_load):
        mock_image1 = Mock()
        mock_image2 = Mock()
        mock_image1.unmask.return_value = Mock()
        mock_image2.unmask.return_value = Mock()
        mock_load.side_effect = [mock_image1, mock_image2]

        result = union_binary_images(["img1.json", "img2.json"], "/tmp")

        assert result["image_filename"] == "union.json"

    @patch("geospatial.geo_operations.load_vector_data")
    @patch("geospatial.geo_operations.save_ee_object")
    def test_intersect_binary_images(self, mock_save, mock_load):
        mock_image1 = Mock()
        mock_image2 = Mock()
        mock_image1.And.return_value = Mock()
        mock_load.side_effect = [mock_image1, mock_image2]

        result = intersect_binary_images(["img1.json", "img2.json"], "/tmp")

        mock_image1.And.assert_called_once_with(mock_image2)
        assert result["image_filename"] == "intersection.json"

    def test_empty_image_list_errors(self):
        with pytest.raises(ValueError, match="No binary images provided"):
            union_binary_images([], "/tmp")
        with pytest.raises(ValueError, match="No binary images provided"):
            intersect_binary_images([], "/tmp")


class TestFeatureCollectionOperations:
    @patch("geospatial.geo_operations.load_vector_data")
    @patch("geospatial.geo_operations.save_ee_object")
    @patch("geospatial.geo_operations.intersect_feature")
    def test_intersect_feature_collections(
        self, mock_intersect_feature, mock_save, mock_load
    ):
        mock_fc1 = Mock(spec=FeatureCollection)
        mock_fc2 = Mock(spec=FeatureCollection)
        mock_fc1.map.return_value = Mock()
        mock_load.side_effect = [mock_fc1, mock_fc2]

        result = intersect_feature_collections(["fc1.json", "fc2.json"], "/tmp")

        mock_fc1.map.assert_called_once()
        assert result["feature_collection_filename"] == "intersection.json"

    @patch("geospatial.geo_operations.load_vector_data")
    @patch("geospatial.geo_operations.save_ee_object")
    def test_merge_feature_collections(self, mock_save, mock_load):
        mock_fc1 = Mock(spec=FeatureCollection)
        mock_fc2 = Mock(spec=FeatureCollection)
        mock_fc1.merge.return_value = Mock()
        mock_load.side_effect = [mock_fc1, mock_fc2]

        result = merge_feature_collections(["fc1.json", "fc2.json"], "/tmp")

        mock_fc1.merge.assert_called_once_with(mock_fc2)
        assert result["feature_collection_filename"] == "union.json"

    def test_empty_fc_list_errors(self):
        with pytest.raises(ValueError, match="No feature collections provided"):
            intersect_feature_collections([], "/tmp")
        with pytest.raises(ValueError, match="No feature collections provided"):
            merge_feature_collections([], "/tmp")


class TestReduceAndMap:
    @patch("geospatial.geo_operations.load_vector_data")
    @patch("geospatial.geo_operations.Reducer")
    def test_reduce_image(self, mock_reducer, mock_load):
        mock_image = Mock()
        mock_fc = Mock()
        mock_reduced = Mock()
        mock_reduced.getInfo.return_value = {"features": [{"properties": {"sum": 100}}]}
        mock_image.reduceRegions.return_value = mock_reduced
        mock_load.side_effect = [mock_image, mock_fc]
        getattr(mock_reducer, "sum").return_value = Mock()

        result = reduce_image("image.json", "fc.json", "sum", "/tmp", 100)

        assert result["total_sum"] == 100
        assert result["input_arguments"]["reducer"] == "sum"

    @patch("geospatial.geo_operations.load_vector_data")
    @patch("geospatial.geo_operations.image_to_html")
    def test_build_map(self, mock_image_to_html, mock_load):
        mock_load.side_effect = [Mock(), Mock(), Mock()]
        mock_image_to_html.return_value = "map.html"

        result = build_map(
            ["img1.json", "img2.json"],
            "fc.json",
            [["#ff0000"]],
            ["Layer 1", "Layer 2"],
            "/tmp",
        )

        assert result["map_filename"] == "map.html"


class TestIntersectFeature:
    @patch("geospatial.geo_operations.ErrorMargin")
    @patch("geospatial.geo_operations.Feature")
    def test_intersect_feature(self, mock_feature_class, mock_error_margin):
        mock_feature1 = Mock(spec=Feature)
        mock_feature2 = Mock(spec=Feature)
        mock_geom1 = Mock()
        mock_geom2 = Mock()
        mock_feature1.geometry.return_value = mock_geom1
        mock_feature2.geometry.return_value = mock_geom2
        mock_geom1.intersection.return_value = Mock()
        mock_result = Mock()
        mock_feature_class.return_value = mock_result
        mock_result.copyProperties.return_value = mock_result

        result = intersect_feature(mock_feature1, mock_feature2)

        mock_geom1.intersection.assert_called_once()
        assert result == mock_result


class TestDemographicFunctions:
    @patch("geospatial.demographic.get_country_code")
    @patch("geospatial.demographic.FeatureCollection")
    @patch("geospatial.demographic.Filter")
    @patch("geospatial.demographic.save_ee_object")
    def test_get_zone_of_area(
        self, mock_save, mock_filter, mock_fc, mock_get_country_code
    ):
        mock_get_country_code.return_value = "USA"
        mock_filter.eq.return_value = Mock()
        mock_fc_instance = Mock()
        mock_fc_instance.filter.return_value = Mock()
        mock_fc.return_value = mock_fc_instance

        result = get_zone_of_area("United States", "country", "/tmp")

        assert result["value"] == "map_zones_feature_collection_USA.json"

    @patch("geospatial.demographic.FeatureCollection")
    @patch("geospatial.demographic.Filter")
    @patch("geospatial.demographic.save_ee_object")
    def test_get_zone_of_area_admin1(self, mock_save, mock_filter, mock_fc):
        """Test getting admin level 1 area."""
        mock_filter.eq.return_value = Mock()
        mock_fc_instance = Mock()
        mock_fc_instance.filter.return_value = Mock()
        mock_fc.return_value = mock_fc_instance

        result = get_zone_of_area("California", "admin1", "/tmp")

        assert result["value"] == "map_zones_feature_collection_California.json"
        assert result["input_arguments"]["area_name"] == "California"
        assert result["input_arguments"]["area_type"] == "admin1"

    @patch("geospatial.demographic.pycountry")
    def test_standarize_country_name(self, mock_pycountry):
        mock_country = Mock()
        mock_country.name = "United States"
        mock_pycountry.countries.get.return_value = mock_country

        result = standarize_country_name("US")

        assert result == "United States"

    @patch("geospatial.demographic.pycountry")
    def test_standarize_country_name_by_alpha3(self, mock_pycountry):
        """Test standardizing country name by alpha-3 code."""
        mock_country = Mock()
        mock_country.name = "United States"
        mock_pycountry.countries.get.side_effect = [None, None, mock_country]

        result = standarize_country_name("USA")

        assert result == "United States"

    @patch("geospatial.demographic.pycountry")
    def test_standarize_country_name_not_found(self, mock_pycountry):
        """Test standardizing country name when not found."""
        mock_pycountry.countries.get.return_value = None

        result = standarize_country_name("INVALID")

        assert result == "INVALID"

    @patch("geospatial.demographic.pycountry")
    def test_standarize_country_name_key_error(self, mock_pycountry):
        """Test standardizing country name with KeyError."""
        mock_pycountry.countries.get.side_effect = KeyError("Country not found")

        result = standarize_country_name("INVALID")

        assert result == "INVALID"

    @patch("geospatial.demographic.standarize_country_name")
    @patch("geospatial.demographic.pycountry")
    def test_get_country_code(self, mock_pycountry, mock_standardize):
        mock_standardize.return_value = "United States"
        mock_country = Mock()
        mock_country.alpha_3 = "USA"
        mock_pycountry.countries.get.return_value = mock_country

        result = get_country_code("US")

        assert result == "USA"

    @patch("geospatial.demographic.standarize_country_name")
    @patch("geospatial.demographic.pycountry")
    def test_get_country_code_not_found(self, mock_pycountry, mock_standardize):
        """Test getting country code when country not found."""
        mock_standardize.return_value = "Invalid Country"
        mock_pycountry.countries.get.return_value = None

        result = get_country_code("INVALID")

        assert result == "Invalid Country"

    @patch("geospatial.demographic.standarize_country_name")
    @patch("geospatial.demographic.pycountry")
    def test_get_country_code_key_error(self, mock_pycountry, mock_standardize):
        """Test getting country code with KeyError."""
        mock_standardize.return_value = "Invalid Country"
        mock_pycountry.countries.get.side_effect = KeyError("Country not found")

        result = get_country_code("INVALID")

        assert result == "Invalid Country"


class TestEarthEngineFunctions:
    @patch("geospatial.earth_engine.DATASETS_METADATA")
    def test_get_dataset_metadata(self, mock_datasets_metadata):
        mock_metadata = Mock()
        mock_metadata.input_arguments = None
        mock_datasets_metadata.__getitem__.return_value = mock_metadata

        result = get_dataset_metadata(ALL_DATASETS.RIVER_FLOOD)

        assert result.input_arguments == {"dataset": ALL_DATASETS.RIVER_FLOOD}

    @patch("geospatial.earth_engine.storage.Client")
    def test_create_bucket(self, mock_storage_client_class):
        """Test creating a new bucket."""
        mock_client = Mock()
        mock_bucket = Mock()
        mock_new_bucket = Mock()

        mock_storage_client_class.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_client.create_bucket.return_value = mock_new_bucket

        result = create_bucket("test-bucket", "test-project")

        mock_storage_client_class.assert_called_once_with(project="test-project")
        mock_client.bucket.assert_called_once_with("test-bucket")
        assert mock_bucket.storage_class == "COLDLINE"
        mock_client.create_bucket.assert_called_once_with(mock_bucket, location="us")
        assert result == mock_new_bucket

    @patch("geospatial.earth_engine.storage.Client")
    def test_upload_blob(self, mock_storage_client_class):
        """Test uploading a blob to GCS."""
        mock_client = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()

        mock_storage_client_class.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob

        upload_blob("test-bucket", "local/file.txt", "remote/file.txt", "test-project")

        mock_storage_client_class.assert_called_once_with(project="test-project")
        mock_client.bucket.assert_called_once_with("test-bucket")
        mock_bucket.blob.assert_called_once_with("remote/file.txt")
        mock_blob.upload_from_filename.assert_called_once_with("local/file.txt")

    @patch("geospatial.earth_engine.upload_blob")
    @patch("os.listdir")
    @patch("os.path.isfile")
    @patch("os.path.isdir")
    def test_upload_directory_files_only(
        self, mock_isdir, mock_isfile, mock_listdir, mock_upload_blob
    ):
        """Test uploading directory with files only."""
        mock_listdir.return_value = ["file1.txt", "file2.txt"]
        mock_isfile.side_effect = [True, True]
        mock_isdir.side_effect = [False, False]

        upload_directory("test-bucket", "source/dir", "dest/dir", "test-project")

        assert mock_upload_blob.call_count == 2
        mock_upload_blob.assert_any_call(
            "test-bucket", "source/dir/file1.txt", "dest/dir/file1.txt", "test-project"
        )
        mock_upload_blob.assert_any_call(
            "test-bucket", "source/dir/file2.txt", "dest/dir/file2.txt", "test-project"
        )

    @patch("geospatial.earth_engine.upload_directory")
    @patch("os.listdir")
    @patch("os.path.isfile")
    @patch("os.path.isdir")
    def test_upload_directory_recursive(
        self, mock_isdir, mock_isfile, mock_listdir, mock_upload_directory
    ):
        """Test uploading directory recursively."""
        mock_listdir.return_value = ["subdir"]
        mock_isfile.return_value = False
        mock_isdir.return_value = True

        mock_upload_directory.return_value = None

        upload_directory("test-bucket", "source/dir", "dest/dir", "test-project")

        mock_upload_directory.assert_called_once_with(
            "test-bucket", "source/dir/subdir", "dest/dir/subdir", "test-project"
        )

    @patch("geospatial.earth_engine.ee.data.startIngestion")
    @patch("geospatial.earth_engine.ee.data.newTaskId")
    @patch("geospatial.earth_engine.storage.Client")
    def test_upload_to_ee_from_gcs_success(
        self, mock_storage_client_class, mock_new_task_id, mock_start_ingestion
    ):
        """Test successful upload to EE from GCS."""
        mock_client = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_blob.exists.return_value = True

        mock_storage_client_class.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_new_task_id.return_value = ["task123"]
        mock_start_ingestion.return_value = {"task_id": "task123"}

        result = upload_to_ee_from_gcs(
            "test-bucket", "file.tif", "users/test/asset", "test-project"
        )

        mock_blob.exists.assert_called_once()
        mock_new_task_id.assert_called_once()
        mock_start_ingestion.assert_called_once()
        assert result == {"task_id": "task123"}

    @patch("geospatial.earth_engine.storage.Client")
    def test_upload_to_ee_from_gcs_file_not_found(self, mock_storage_client_class):
        """Test upload to EE when file doesn't exist in GCS."""
        mock_client = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_blob.exists.return_value = False

        mock_storage_client_class.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob

        with pytest.raises(FileNotFoundError, match="File not found in GCS"):
            upload_to_ee_from_gcs(
                "test-bucket", "nonexistent.tif", "users/test/asset", "test-project"
            )

    @patch("geospatial.earth_engine.ee.data.createAsset")
    @patch("os.path.dirname")
    @patch("os.path.join")
    def test_create_ee_asset_path_success(
        self, mock_join, mock_dirname, mock_create_asset
    ):
        """Test creating EE asset path successfully."""
        mock_dirname.return_value = "folder/subfolder"
        mock_join.return_value = "users/test/folder/subfolder"

        create_ee_asset_path("users/test", "folder/subfolder/file.tif")

        mock_create_asset.assert_called_once_with(
            {"type": "FOLDER"}, "users/test/folder/subfolder"
        )

    @patch("geospatial.earth_engine.ee.data.createAsset")
    @patch("geospatial.earth_engine.ee.ee_exception.EEException", new=Exception)
    @patch("os.path.dirname")
    @patch("os.path.join")
    def test_create_ee_asset_path_already_exists(
        self, mock_join, mock_dirname, mock_create_asset
    ):
        """Test creating EE asset path when folder already exists."""
        mock_dirname.return_value = "folder/subfolder"
        mock_join.return_value = "users/test/folder/subfolder"
        mock_create_asset.side_effect = Exception("Folder already exists")

        create_ee_asset_path("users/test", "folder/subfolder/file.tif")

        mock_create_asset.assert_called_once()

    @patch("geospatial.earth_engine.upload_to_ee_from_gcs")
    @patch("geospatial.earth_engine.create_ee_asset_path")
    @patch("geospatial.earth_engine.storage.Client")
    @patch("os.path.join")
    def test_upload_bucket_to_ee(
        self,
        mock_join,
        mock_storage_client_class,
        mock_create_asset_path,
        mock_upload_to_ee,
    ):
        """Test uploading entire bucket to EE."""
        mock_client = Mock()
        mock_bucket = Mock()
        mock_blob1 = Mock()
        mock_blob1.name = "file1.tif"
        mock_blob2 = Mock()
        mock_blob2.name = "folder/file2.tif"

        mock_storage_client_class.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.list_blobs.return_value = [mock_blob1, mock_blob2]
        mock_create_asset_path.return_value = "created/path"
        mock_upload_to_ee.side_effect = [{"task1": "result1"}, {"task2": "result2"}]
        mock_join.side_effect = lambda *args: "/".join(args)

        result = upload_bucket_to_ee("test-bucket", "test-project", "users/test")

        assert len(result) == 2
        assert mock_upload_to_ee.call_count == 2


class TestImageOperationsUnhappyPaths:
    @patch("geospatial.geo_operations.load_vector_data")
    def test_mask_image_invalid_mask_type(self, mock_load):
        """Test mask_image with invalid mask type."""
        mock_load.side_effect = [Mock(spec=Image), Mock()]

        with pytest.raises(TypeError, match="Expected an Earth Engine Image object"):
            mask_image("image.json", "mask.json", "/tmp")

    @patch("geospatial.geo_operations.load_vector_data")
    @patch("geospatial.geo_operations.save_ee_object")
    @patch("geospatial.geo_operations.ee.Number")
    def test_filter_image_zero_threshold(self, mock_number, mock_save, mock_load):
        """Test filtering image with zero threshold."""
        mock_image = Mock(spec=Image)
        mock_filtered = Mock()
        mock_image.gt.return_value = mock_filtered
        mock_load.return_value = mock_image
        mock_number.return_value = Mock()

        result = filter_image_by_threshold("image.json", 0.0, "/tmp")

        mock_image.gt.assert_called_once()
        assert result["input_arguments"]["threshold"] == 0.0

    def test_union_binary_images_single_image(self):
        """Test union with single image."""
        with (
            patch("geospatial.geo_operations.load_vector_data") as mock_load,
            patch("geospatial.geo_operations.save_ee_object") as mock_save,
        ):

            mock_image = Mock()
            mock_image.unmask.return_value = Mock()
            mock_load.return_value = mock_image

            result = union_binary_images(["img1.json"], "/tmp")

            assert result["image_filename"] == "union.json"
            mock_image.unmask.assert_called_once_with(0)

    def test_intersect_binary_images_single_image(self):
        """Test intersection with single image."""
        with (
            patch("geospatial.geo_operations.load_vector_data") as mock_load,
            patch("geospatial.geo_operations.save_ee_object") as mock_save,
        ):

            mock_image = Mock()
            mock_load.return_value = mock_image

            result = intersect_binary_images(["img1.json"], "/tmp")

            assert result["image_filename"] == "intersection.json"


class TestFeatureCollectionUnhappyPaths:
    @patch("geospatial.geo_operations.load_vector_data")
    def test_intersect_feature_collections_with_image(self, mock_load):
        """Test intersecting feature collections when first item is an image."""
        mock_image = Mock(spec=Image)
        mock_load.return_value = mock_image

        with pytest.raises(ValueError, match="Image cannot be intersected"):
            intersect_feature_collections(["img1.json", "fc2.json"], "/tmp")

    @patch("geospatial.geo_operations.load_vector_data")
    def test_intersect_feature_collections_second_item_is_image(self, mock_load):
        """Test intersecting feature collections when second item is an image."""
        mock_fc = Mock(spec=FeatureCollection)
        mock_image = Mock(spec=Image)
        mock_load.side_effect = [mock_fc, mock_image]

        with pytest.raises(ValueError, match="Image cannot be intersected"):
            intersect_feature_collections(["fc1.json", "img2.json"], "/tmp")

    @patch("geospatial.geo_operations.load_vector_data")
    def test_merge_feature_collections_with_image(self, mock_load):
        """Test merging feature collections when first item is an image."""
        mock_image = Mock(spec=Image)
        mock_load.return_value = mock_image

        with pytest.raises(ValueError, match="Image cannot be unioned"):
            merge_feature_collections(["img1.json", "fc2.json"], "/tmp")

    @patch("geospatial.geo_operations.load_vector_data")
    def test_merge_feature_collections_second_item_is_image(self, mock_load):
        """Test merging feature collections when second item is an image."""
        mock_fc = Mock(spec=FeatureCollection)
        mock_image = Mock(spec=Image)
        mock_load.side_effect = [mock_fc, mock_image]

        with pytest.raises(ValueError, match="Image cannot be unioned"):
            merge_feature_collections(["fc1.json", "img2.json"], "/tmp")

    def test_intersect_feature_collections_single_collection(self):
        """Test intersecting with single feature collection."""
        with (
            patch("geospatial.geo_operations.load_vector_data") as mock_load,
            patch("geospatial.geo_operations.save_ee_object") as mock_save,
        ):

            mock_fc = Mock(spec=FeatureCollection)
            mock_load.return_value = mock_fc

            result = intersect_feature_collections(["fc1.json"], "/tmp")

            assert result["feature_collection_filename"] == "intersection.json"

    def test_merge_feature_collections_single_collection(self):
        """Test merging single feature collection."""
        with (
            patch("geospatial.geo_operations.load_vector_data") as mock_load,
            patch("geospatial.geo_operations.save_ee_object") as mock_save,
        ):

            mock_fc = Mock(spec=FeatureCollection)
            mock_load.return_value = mock_fc

            result = merge_feature_collections(["fc1.json"], "/tmp")

            assert result["feature_collection_filename"] == "union.json"


class TestReduceAndMapUnhappyPaths:
    @patch("geospatial.geo_operations.load_vector_data")
    @patch("geospatial.geo_operations.Reducer")
    def test_reduce_image_empty_results(self, mock_reducer, mock_load):
        """Test reduce_image with empty results."""
        mock_image = Mock()
        mock_fc = Mock()
        mock_reduced = Mock()
        mock_reduced.getInfo.return_value = {"features": []}
        mock_image.reduceRegions.return_value = mock_reduced
        mock_load.side_effect = [mock_image, mock_fc]
        getattr(mock_reducer, "sum").return_value = Mock()

        result = reduce_image("image.json", "fc.json", "sum", "/tmp", 100)

        assert result["total_sum"] == 0

    @patch("geospatial.geo_operations.load_vector_data")
    @patch("geospatial.geo_operations.Reducer")
    def test_reduce_image_missing_sum_property(self, mock_reducer, mock_load):
        """Test reduce_image when features don't have sum property."""
        mock_image = Mock()
        mock_fc = Mock()
        mock_reduced = Mock()
        mock_reduced.getInfo.return_value = {"features": [{"properties": {}}]}
        mock_image.reduceRegions.return_value = mock_reduced
        mock_load.side_effect = [mock_image, mock_fc]
        getattr(mock_reducer, "sum").return_value = Mock()

        with pytest.raises(KeyError):
            reduce_image("image.json", "fc.json", "sum", "/tmp", 100)

    @patch("geospatial.geo_operations.load_vector_data")
    @patch("geospatial.geo_operations.image_to_html")
    def test_build_map_mismatched_names_length(self, mock_image_to_html, mock_load):
        """Test build_map with mismatched names and images length."""
        mock_load.side_effect = [Mock(), Mock(), Mock()]
        mock_image_to_html.return_value = "map.html"

        with pytest.raises(
            ValueError,
            match="The number of names must be equal to the number of images",
        ):
            build_map(
                ["img1.json", "img2.json"],
                "fc.json",
                [["#ff0000"]],
                ["Layer 1"],
                "/tmp",
            )

    @patch("geospatial.geo_operations.load_vector_data")
    @patch("geospatial.geo_operations.image_to_html")
    def test_build_map_empty_names(self, mock_image_to_html, mock_load):
        """Test build_map with empty names list and empty images."""
        mock_load.return_value = Mock()
        mock_image_to_html.return_value = "map.html"

        result = build_map(
            [],
            "fc.json",
            [],
            [],
            "/tmp",
        )

        assert result["map_filename"] == "map.html"


class TestGetDatasetUnhappyPaths:
    @patch("geospatial.geo_operations.get_dataset_metadata")
    @patch("geospatial.geo_operations.save_ee_object")
    @patch("geospatial.geo_operations.ImageCollection")
    def test_get_dataset_mosaic_with_exception(
        self, mock_image_collection, mock_save, mock_get_metadata
    ):
        """Test getting dataset with mosaic when ImageCollection raises exception."""
        mock_metadata = Mock()
        mock_metadata.asset_id = "invalid/asset"
        mock_metadata.mosaic = True
        mock_metadata.image_filename = "test_image.json"
        mock_metadata.model_dump.return_value = {
            "asset_id": "invalid/asset",
            "image_filename": "test_image.json",
            "description": "Test dataset",
        }
        mock_get_metadata.return_value = mock_metadata
        mock_image_collection.side_effect = Exception("Asset not found")

        with pytest.raises(Exception, match="Asset not found"):
            get_dataset_image_and_metadata(ALL_DATASETS.RIVER_FLOOD, "/tmp")


class TestHazardsMetadataUnhappyPaths:
    @patch("geospatial.hazards_metadata.load_index_from_storage")
    @patch("geospatial.hazards_metadata.StorageContext")
    @patch("geospatial.hazards_metadata.VectorIndexRetriever")
    def test_get_ccri_metadata_storage_error(
        self, mock_retriever_class, mock_storage_context, mock_load_index
    ):
        """Test get_ccri_metadata when storage context fails."""
        mock_storage_context.from_defaults.side_effect = Exception("Storage not found")

        with pytest.raises(Exception, match="Storage not found"):
            get_ccri_metadata("test query")

    @patch("geospatial.hazards_metadata.load_index_from_storage")
    @patch("geospatial.hazards_metadata.StorageContext")
    @patch("geospatial.hazards_metadata.VectorIndexRetriever")
    def test_get_ccri_metadata_retrieval_error(
        self, mock_retriever_class, mock_storage_context, mock_load_index
    ):
        """Test get_ccri_metadata when retrieval fails."""
        mock_storage_context.from_defaults.return_value = Mock()
        mock_load_index.return_value = Mock()
        mock_retriever = Mock()
        mock_retriever_class.return_value = mock_retriever
        mock_retriever.retrieve.side_effect = Exception("Retrieval failed")

        with pytest.raises(Exception, match="Retrieval failed"):
            get_ccri_metadata("test query")

    @patch("geospatial.hazards_metadata.load_index_from_storage")
    @patch("geospatial.hazards_metadata.StorageContext")
    @patch("geospatial.hazards_metadata.VectorIndexRetriever")
    def test_get_ccri_metadata_empty_results(
        self, mock_retriever_class, mock_storage_context, mock_load_index
    ):
        """Test get_ccri_metadata with empty retrieval results."""
        mock_storage_context.from_defaults.return_value = Mock()
        mock_load_index.return_value = Mock()
        mock_retriever = Mock()
        mock_retriever_class.return_value = mock_retriever
        mock_retriever.retrieve.return_value = []

        result = get_ccri_metadata("test query")

        assert result == ""


class TestIntersectFeatureUnhappyPaths:
    @patch("geospatial.geo_operations.ErrorMargin")
    @patch("geospatial.geo_operations.Feature")
    def test_intersect_feature_geometry_error(
        self, mock_feature_class, mock_error_margin
    ):
        """Test intersect_feature when geometry intersection fails."""
        mock_feature1 = Mock(spec=Feature)
        mock_feature2 = Mock(spec=Feature)
        mock_geom1 = Mock()
        mock_geom2 = Mock()
        mock_feature1.geometry.return_value = mock_geom1
        mock_feature2.geometry.return_value = mock_geom2
        mock_geom1.intersection.side_effect = Exception("Geometry error")

        with pytest.raises(Exception, match="Geometry error"):
            intersect_feature(mock_feature1, mock_feature2)

    @patch("geospatial.geo_operations.ErrorMargin")
    @patch("geospatial.geo_operations.Feature")
    def test_intersect_feature_copy_properties_error(
        self, mock_feature_class, mock_error_margin
    ):
        """Test intersect_feature when copyProperties fails."""
        mock_feature1 = Mock(spec=Feature)
        mock_feature2 = Mock(spec=Feature)
        mock_geom1 = Mock()
        mock_geom2 = Mock()
        mock_feature1.geometry.return_value = mock_geom1
        mock_feature2.geometry.return_value = mock_geom2
        mock_geom1.intersection.return_value = Mock()
        mock_result = Mock()
        mock_feature_class.return_value = mock_result
        mock_result.copyProperties.side_effect = Exception("Copy properties error")

        with pytest.raises(Exception, match="Copy properties error"):
            intersect_feature(mock_feature1, mock_feature2)
