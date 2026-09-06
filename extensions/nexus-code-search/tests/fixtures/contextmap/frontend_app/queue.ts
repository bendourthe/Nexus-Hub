import { Queue } from "bullmq";
import { EventEmitter } from "events";

const jobs = new Queue("jobs");
const bus = new EventEmitter();

export { bus, jobs };
