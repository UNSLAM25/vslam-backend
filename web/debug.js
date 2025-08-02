function showDebugInfo(uint8Buffer) {
    console.log("------------- Debug ------------- ");
    byteLength = uint8Buffer.byteLength;
    length = uint8Buffer.length; // = byteLength
    console.log("uint8Buffer byteLength and length: ", byteLength, length); // Always the same
    console.log("Last byte: ", uint8Buffer[length - 1]); // Always 255
    console.log("1st row:", uint8Buffer.slice(0, 32));
    //console.log("last row:", uint8Buffer.slice(length-38,length));
    dataView = new DataView(uint8Buffer.buffer);
    dataViewByteLength = dataView.byteLength;
    console.log("dataViewByteLength:", dataViewByteLength);
    for (i = 0; i < 5; i++) {
      console.log(
        i,
        dataView.getFloat32(dataViewByteLength - 38 + 4 * i, true)
      );
    }

    let descriptorSum = 0;
    for (let i = 0; i < 32; i++) {
      descriptorSum += uint8Buffer[i];
    }
    let debugSum = dataView.getFloat32(dataViewByteLength - 22, true); // index 4 float, last row: -38+4*4 = -22
    if (debugSum != descriptorSum) {
      console.log(
        "ERROR in descriptor checksum (desc, debug):",
        descriptorSum,
        debugSum
      );
    } else {
      console.log("Descriptors are fine!");
    }
}