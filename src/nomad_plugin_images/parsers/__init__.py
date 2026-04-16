from nomad.config.models.plugins import ParserEntryPoint


class ImageParserEntryPoint(ParserEntryPoint):
    """Entry point for the Image Analysis parser."""

    def load(self):
        from nomad_plugin_images.parsers.image_parser import ImageParser

        return ImageParser(**self.model_dump())


class ManifestParserEntryPoint(ParserEntryPoint):
    """Entry point for the Image Manifest parser."""

    def load(self):
        from nomad_plugin_images.parsers.manifest_parser import ManifestParser

        return ManifestParser(**self.model_dump())


image_parser = ImageParserEntryPoint(
    name='ImageParser',
    description='Parser for image analysis data with metadata.json files.',
    mainfile_name_re=r'metadata\.json',
    mainfile_mime_re=r'application/json',
)

manifest_parser = ManifestParserEntryPoint(
    name='ImageManifestParser',
    description='Parser for image experiment manifest CSV files with multiple image steps.',
    mainfile_name_re=r'.+_manifest\.csv',
    mainfile_mime_re=r'text/csv',
)

parser_entry_point = image_parser
