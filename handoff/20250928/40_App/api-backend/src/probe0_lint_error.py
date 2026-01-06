from flask import Flask,request

app = Flask(__name__)

@app.route('/api/v1/resource', methods=['GET'])
def get_resource():
    resource_id = request.args.get('id')
    if resource_id == None:
        return {'error': 'Missing resource id'}, 400
    else:
        return {'data': {'id': resource_id, 'name': 'Resource Name'}}, 200

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=8080)