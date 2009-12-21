<?php
/**
 * This is the mothership file. Create an instance of this and you'll have access to the API methods defined below.
 * Add new API methods as they become available. Each method contains documentation about the params and return values.
 */

require_once('appmail.config.php');
require_once('helpers'.DIRECTORY_SEPARATOR.'appmail.rest.php');

class AppMailCore
{
	var $AppMailRest;
	var $api_key;
	var $url;

	/**
	 * Initialises AppMailCore. Optionally provide runtime api key and url.
	 */
	function AppMailCore($api_key = APPMAIL_API_KEY, $url = APPMAIL_URL) {
		$this->url = $url;
		$this->api_key = $api_key;
    $this->AppMailRest = new AppMailRest($this->url);
	}

	/**
	 * Asynchronously sends an email using Google App Engine
	 *
	 * Params are fairly self explanatory. However, note that the "from" address must be a registered email with
	 * your Google App Engine account.
	 */
	function send($to, $from, $subject, $body) {
		$api_key = $this->api_key;
		$status = $this->AppMailRest->post('send', compact('api_key','to','from','subject','body'));
		return $status;
	}
}
?>
