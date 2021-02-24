const noble = require('@abandonware/noble');

async function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

function zeroPadding(num,length){
    return ('0000000000' + num).slice(-length);
}

function dateTimeFormat(year, month, day, hour, min, sec) {
  return zeroPadding(year, 4) + '-' +zeroPadding(month, 2) + '-' + zeroPadding(day, 2)
    + ' ' + zeroPadding(hour, 2) + ':' + zeroPadding(min, 2) + ':' + zeroPadding(sec, 2);
}

var buffer;
function on_notify(data, isNotification) {
  if (data[0] === 0xaa) {
    buffer = data;
  } else {
    buffer += data;
    buffer = Buffer.from(buffer, 'ascii');
    //console.log(buffer);
    const v = buffer.readInt32LE(5)/Math.pow(16, 6);
    const c = buffer.readInt32LE(11)/Math.pow(32, 6) * 1000;
    const w = buffer.readInt32LE(17)/Math.pow(16, 6);
    const sec   = buffer[23];
    const min   = buffer[24];
    const hour  = buffer[25];
    const day   = buffer[26];
    const month = buffer[27];
    const year  = buffer[28] + 1900;
    const dateTime = dateTimeFormat(year, month, day, hour, min, sec);
    console.log(dateTime + ' ' + v.toFixed(1) + '[V] ' + c.toFixed(1) + '[mA] ' + w.toFixed(1) + '[W]');
  } 
}

noble.on('stateChange', async (state) => {
  if (state === 'poweredOn') {
    noble.startScanning([] , true);
  }
});

noble.on('discover', async (peripheral) => {
  //console.log(`${peripheral.address} (${peripheral.advertisement.localName})`);
  if (peripheral.id === process.argv[2]) {
    await noble.stopScanningAsync();
    await peripheral.connectAsync();
 
    const services = await peripheral.discoverServicesAsync(['6e400001b5a3f393e0a9e50e24dcca9e']); 
    const service = services[0];
    //console.log(service);

    const chars = await service.discoverCharacteristicsAsync();
    const tx_char = chars[0];
    const rx_char = chars[1];
    //console.log(chars);
    
    //const tx_chars = await service.discoverCharacteristicsAsync(['6e400002b5a3f393e0a9e50e24dcca9e']);
    //const tx_char = tx_chars[0]
    //console.log(tx_chars)

    //const rx_chars = await service.discoverCharacteristicsAsync(['6e400003b5a3f393e0a9e50e24dcca9e']);
    //const rx_char = rx_chars[0]
    //console.log(rx_char)

    rx_char.on('data', on_notify);
    //console.log('added callback')

    rx_char.subscribe(function(error) {
        console.log('subscribe error: ' + error);
    });
    console.log('subscribed')
    //rx_char.notify(true);
 
    while (true) {
        const buffer = Buffer.from([0xaa, 0x00, 0x01, 0x08, 0xb3]);
        await tx_char.writeAsync(buffer, true);
        //console.log('write');
        await sleep(1000);
    }
  }
});

if (process.argv.length < 3) {
  console.error("usage: %s %s id", process.argv[0], process.argv[1]);
  process.exit(-1)
}
