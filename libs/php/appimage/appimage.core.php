<?php
/**
 * This is the mothership file. Create an instance of this and you'll have access to the API methods defined below.
 * Each method contains documentation about the params and return values.
 */

require_once('appimage.config.php');
require_once('helpers'.DIRECTORY_SEPARATOR.'appimage.rest.php');

class AppImageCore
{
	var $AppImageRest;
	var $api_key;
	var $url;

	/**
	 * Initialises AppImageCore. Optionally provide runtime api key and url.
	 */
	function AppImageCore($api_key = APPIMAGE_API_KEY, $url = APPIMAGE_URL) {
		$this->url = $url;
		$this->api_key = $api_key;
    $this->AppImageRest = new AppImageRest($this->url);
	}

	/**
	 * Uploads an image into the GAE datastore.
	 *
	 * @param type    either "avatar" or "photo" (or any other model you've custom added)
	 * @param file    the tmp location ($_FILES['tmp_name']) of the uploaded php file (ie, /private/var/tmp/phpRDJST9)
	 * @param img_id  a unique id to assign to the image, for an avatar this might relate to a username/user_id in your db.
	 */
	function upload($type, $file, $img_id) {
		$image = '@'.$file;
		$api_key = $this->api_key;
		$image_key = $this->AppImageRest->post('upload/'.$type, compact('api_key','image','img_id'));
		return $image_key;
	}

	/**
	 * Returns an array of URLs for viewing the different image sizes.
	 * You can now use it in your php rendering (ie, <img src="<?php echo $urls['thumb'] ?>" alt="thumbnail" />)
	 *
	 * @param type    either "avatar" or "photo" (or any other model you've custom added)
	 * @param img_id  unique id for the image (assigned on upload). This is not a GAE UUID.
	 */
	function getUrls($type, $img_id) {
		$urls = array(
			'source' => $this->url.'view/'.$type.'/source/'.$img_id,
			'image' => $this->url.'view/'.$type.'/image/'.$img_id,
			'thumb' => $this->url.'view/'.$type.'/thumb/'.$img_id
		);
		return $urls;
	}

	/**
	 * Crops the image specified using the original uploaded source file as the basis.
	 * After transforming it regenerates the thumbnail image.
	 *
	 * @param type          either "avatar" or "photo" (or any other model you've custom added)
	 * @param img_id        unique id for the image (assigned on upload). This is not a GAE UUID.
	 * @param x1,y1,x2,y2   coordinates (in pixels or percentages).	If percentages, then number between 0.0 and 1.0.
	 * @param unit          either "pixels" or "percentage"
	 */
	function crop($type, $img_id, $x1, $y1, $x2, $y2, $unit) {
		$params = array('img_id' => $img_id,
		                'x1' => $x1,
		                'y1' => $y1,
		                'x2' => $x2,
		                'y2' => $y2,
		                'unit' => $unit,
		                'api_key' => $this->api_key);

		$url = $this->AppImageRest->get('crop/'.$type, $params);
		return $url;
	}

	/**
	 * Resizes the image specified using the original uploaded source file as the basis.
	 * After transforming it regenerates the thumbnail image.
	 *
	 * NOTE: From http://code.google.com/appengine/docs/python/images/imageclass.html#Image_resize
	 * Resizes an image, scaling down or up to the given width and height. The resize transform preserves
	 * the aspect ratio of the image. If both the width and the height arguments are provided, the transform
	 * uses the dimension that results in a smaller image.
	 *
	 * @param type          either "avatar" or "photo" (or any other model you've custom added)
	 * @param img_id        unique id for the image (assigned on upload). This is not a GAE UUID.
	 * @param width,height  resize to size (in pixels or percentages).	If percentages, then number between 0.0 and 1.0.
	 * @param unit          either "pixels" or "percentage"
	 */
	function resize($type, $img_id, $width, $height, $unit) {
		$params = array('img_id' => $img_id,
		                'width' => $width,
		                'height' => $height,
		                'unit' => $unit,
		                'api_key' => $this->api_key);

		$url = $this->AppImageRest->get('resize/'.$type, $params);
		return $url;
	}
}
?>
