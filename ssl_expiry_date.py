import ssl
import socket
import datetime

def get_ssl_expiry_date(hostname):
    context = ssl.create_default_context()
    conn = context.wrap_socket(socket.socket(socket.AF_INET), server_hostname=hostname)
    conn.settimeout(3.0)  # Set socket timeout
    try:
        conn.connect((hostname, 443))
        ssl_info = conn.getpeercert()
        # Parse the certificate's 'notAfter' value to get the expiry date
        cert_expiry_date = datetime.datetime.strptime(ssl_info['notAfter'], '%b %d %H:%M:%S %Y %Z')
        return cert_expiry_date
    except Exception as e:
        print(f"Error retrieving SSL certificate for {hostname}: {e}")
        return None
    finally:
        conn.close()

# Example usage
if __name__ == "__main__":
    domain = 'example.com'
    expiry_date = get_ssl_expiry_date(domain)
    if expiry_date:
        print(f"SSL certificate for {domain} expires on: {expiry_date}")
