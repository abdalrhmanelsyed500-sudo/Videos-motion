extends RefCounted
## Load source PNGs without editor import; exported projects can use imported
## Texture2D resources. All sprites use the project's nearest-neighbor filter.

static func texture(path: String) -> Texture2D:
	if FileAccess.file_exists(path):
		var image := Image.new()
		if image.load_png_from_buffer(FileAccess.get_file_as_bytes(path)) == OK:
			return ImageTexture.create_from_image(image)
	if ResourceLoader.exists(path):
		return load(path)
	return null
