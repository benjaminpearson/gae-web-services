<?php
/**
 * A REST Helper that prepares and sends data to exposed App API URLs.
 */
class AppMailRest
{
	var $url;

	function AppMailRest($url) {
		$this->url = $url;
	}

	function post($method, $params = array()) {
		try {
			$url = $this->url.$method;
			$response = $this->_httpPost($url, $params);
			return $response;
		} catch (Exception $e) {
			return null;
		}
	}

	function _queryString($params) {
		$url_params = array();
		foreach($params as $key => $value) {
			$url_params[] = urlencode($key).'='.urlencode($value);
		}
		$query_string = implode('&',$url_params);

		return $query_string;
	}

	function _httpPost($url, $data) {
		$c = curl_init();
		curl_setopt($c, CURLOPT_URL, $url);
	 	curl_setopt($c, CURLOPT_POST, 1);
		curl_setopt($c, CURLOPT_SSL_VERIFYPEER, true);
	 	curl_setopt($c, CURLOPT_POSTFIELDS, $data);
		curl_setopt($c, CURLOPT_RETURNTRANSFER, 1);
		$output = curl_exec($c);
		curl_close($c);
		return $output;
	}

}
?>
