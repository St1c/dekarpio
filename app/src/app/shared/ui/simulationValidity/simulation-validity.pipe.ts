import { Pipe, PipeTransform } from '@angular/core';

type ObjectOfObjects = {
  [key: string]: {
    [subKey: string]: {
      [subSubKey: string]: unknown;
    };
  };
};

@Pipe({
  name: 'simulationValidity',
  standalone: true
})
export class SimulationValidityPipe implements PipeTransform {

  transform(value: ObjectOfObjects, ...args: unknown[]): unknown {
    // console.log('simulation validity pipe', value)
    let valid = true;
    const jsonValue = JSON.stringify(value);

    console.time('simulation validity pipe');
    if (jsonValue.includes('Param')) valid = false;
    if (jsonValue.includes('False')) valid = false;
    if (jsonValue.includes('True')) valid = false;
    console.timeEnd('simulation validity pipe');

    // console.time('simulation validity pipe 2')
    // Object.keys(value).forEach(key => {
    //   Object.keys(value[key]).forEach(subKey => {
    //     const params: any = value[key][subKey]['param'];
    //     if (params) {
    //       Object.keys(params[0]).forEach(paramKey => {
    //         // console.log(paramKey)
    //         // console.log(params[paramKey])
    //       });
    //     }
    //     if (Object.keys(value[key][subKey]).includes('Param')) {
    //       valid = false;
    //     }
    //   });
    // });
    // console.timeEnd('simulation validity pipe 2')
  
    return valid ? 'OK' : 'Invalid';
  }

}
