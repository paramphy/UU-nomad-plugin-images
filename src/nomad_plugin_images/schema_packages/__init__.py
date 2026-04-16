from nomad.config.models.plugins import SchemaPackageEntryPoint


class ImageAnalysisEntryPoint(SchemaPackageEntryPoint):
    """Entry point for the Image Analysis schema package."""

    def load(self):
        from nomad_plugin_images.schema_packages.image_analysis import m_package

        return m_package


image_analysis = ImageAnalysisEntryPoint(
    name='Image Analysis',
    description='Schema package for image analysis data (resolution, ROI, metadata)',
)

schema_package_entry_point = image_analysis
